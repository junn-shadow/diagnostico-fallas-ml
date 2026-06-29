import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.config.paths import SAMPLES_DIR, ensure_directories

logging.basicConfig(level=logging.INFO)
from app.correlation.alert_generator import generate_alerts
from app.database.repositories import save_incidents
from app.ingestion.load_logs import profile_log_file
from app.preprocessing.feature_engineering import build_features
from app.services.anomaly_service import enrich_with_anomalies
from app.services.log_service import load_and_parse
from app.services.nlp_service import enrich_with_semantics
from app.config.settings import (
    DEFAULT_CONTAMINATION,
    DEFAULT_DBSCAN_EPS,
    DEFAULT_DBSCAN_MIN_SAMPLES,
)


@dataclass
class PipelineResult:
    logs: pd.DataFrame
    semantic_backend: str
    saved_incidents: int
    profile: dict
    stages: list[dict]
    statistical_backend: str = "unknown"
    semantic_scope: str = "unknown"
    persistence_error: str | None = None
    silhouette_score: float = 0.0
    davies_bouldin_index: float = 0.0
    run_id: str = "unknown"
    log_source: str = "unknown"

    @property
    def anomaly_count(self) -> int:
        return int(self.logs["is_anomaly"].sum())


class PipelineService:
    def run(
        self,
        log_path: str | Path | None = None,
        persist: bool = True,
        contamination: float = DEFAULT_CONTAMINATION,
        clustering_method: str = "auto",
        clustering_eps: float = DEFAULT_DBSCAN_EPS,
        clustering_min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES,
        clustering_n_clusters: int = 5,
        nlp_backend: str = "auto",
        log_source: str | None = None,
    ) -> PipelineResult:
        ensure_directories()
        path = Path(log_path) if log_path else SAMPLES_DIR / "sample.log"

        if not path.exists():
            raise FileNotFoundError(f"Archivo de log no encontrado: {path}")

        # Metadatos únicos para identificar la ejecución
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        log_source = log_source or path.name
        pipeline_start = time.perf_counter()

        stages = []
        logging.info("Iniciando pipeline de análisis de logs (run_id=%s, source=%s)", run_id, log_source)

        # ── Etapa 1: Perfilado ───────────────────────────────────────────
        t0 = time.perf_counter()
        logging.info("Perfilando archivo de logs")
        profile = profile_log_file(path)
        stages.append(
            {
                "stage": "Perfil del archivo",
                "status": "Completado",
                "detail": f"{profile['non_empty_lines']:,} lineas utiles",
                "duration_s": round(time.perf_counter() - t0, 3),
            }
        )

        # ── Etapa 2: Ingestion + Limpieza ──────────────────────────────
        t0 = time.perf_counter()
        logging.info("Cargando y limpiando logs")
        logs = load_and_parse(path)
        if logs.empty:
            raise ValueError(f"El archivo de log está vacío o no contiene líneas válidas: {path}")
        stages.append(
            {
                "stage": "Ingestion + limpieza",
                "status": "Completado",
                "detail": f"{len(logs):,} eventos cargados",
                "duration_s": round(time.perf_counter() - t0, 3),
            }
        )

        # ── Etapa 3: Feature Engineering ──────────────────────────────
        t0 = time.perf_counter()
        logging.info("Construyendo features TF‑IDF y numéricos")
        tfidf, numeric, _ = build_features(logs)
        stages.append(
            {
                "stage": "Drain + features",
                "status": "Completado",
                "detail": f"{tfidf.shape[1]} features TF-IDF",
                "duration_s": round(time.perf_counter() - t0, 3),
            }
        )

        # ── Etapa 4: Detección de Anomalías ────────────────────────────
        t0 = time.perf_counter()
        logging.info("Detectando anomalías con Isolation Forest")
        logs = enrich_with_anomalies(
            logs,
            tfidf,
            numeric,
            contamination=contamination,
            clustering_method=clustering_method,
            clustering_eps=clustering_eps,
            clustering_min_samples=clustering_min_samples,
            clustering_n_clusters=clustering_n_clusters,
        )
        statistical_backend = logs.attrs.get("statistical_cluster_backend", "unknown")
        stages.append(
            {
                "stage": "ML no supervisado",
                "status": "Completado",
                "detail": f"Isolation Forest + {statistical_backend}",
                "duration_s": round(time.perf_counter() - t0, 3),
            }
        )

        # ── Etapa 5: NLP Semántico ─────────────────────────────────────
        t0 = time.perf_counter()
        logging.info("Enriqueciendo logs con embeddings semánticos")
        try:
            logs = enrich_with_semantics(logs, backend=nlp_backend)
            semantic_backend = logs.attrs.get("semantic_backend", "unknown")
            semantic_scope = logs.attrs.get("semantic_scope", "unknown")
            stages.append(
                {
                    "stage": "NLP semantico",
                    "status": "Completado",
                    "detail": f"{semantic_backend} sobre {semantic_scope}",
                    "duration_s": round(time.perf_counter() - t0, 3),
                }
            )
        except Exception as exc:
            logging.warning("Error en NLP semántico: %s. Usando clusters por defecto.", exc)
            semantic_backend = "fallback_none"
            semantic_scope = "N/A"
            if "semantic_cluster" not in logs.columns:
                logs["semantic_cluster"] = -1
            stages.append(
                {
                    "stage": "NLP semantico",
                    "status": "Degradado",
                    "detail": f"Error: {exc.__class__.__name__}",
                    "duration_s": round(time.perf_counter() - t0, 3),
                }
            )

        # ── Etapa 6: Correlación y Alertas ──────────────────────────────
        t0 = time.perf_counter()
        logs.attrs["statistical_cluster_backend"] = statistical_backend
        logging.info("Generando alertas y causas raíz")
        try:
            logs = generate_alerts(logs, nlp_backend=nlp_backend)
        except Exception as exc:
            logging.warning("Error generando alertas: %s. Usando diagnóstico por defecto.", exc)
            if "root_cause" not in logs.columns:
                logs["root_cause"] = "Comportamiento normal"
            if "recommendation" not in logs.columns:
                logs["recommendation"] = "No requiere accion"
            if "severity_label" not in logs.columns:
                logs["severity_label"] = logs["level"].replace({"WARN": "WARNING"})
        stages.append(
            {
                "stage": "Correlacion",
                "status": "Completado",
                "detail": "Causa raiz y recomendaciones",
                "duration_s": round(time.perf_counter() - t0, 3),
            }
        )

        saved = 0
        persistence_error = None
        if persist:
            logging.info("Persistiendo incidentes en SQLite")
            try:
                saved = save_incidents(logs, log_source=log_source, run_id=run_id)
            except Exception as exc:
                persistence_error = str(exc)
                stages.append(
                    {"stage": "Persistencia", "status": "Degradado", "detail": str(exc)}
                )
        else:
            stages.append(
                {
                    "stage": "Persistencia",
                    "status": "Omitido",
                    "detail": "SQLite desactivado",
                }
            )

        total_time = round(time.perf_counter() - pipeline_start, 3)
        logging.info(
            "Pipeline completado en %.3fs (run_id=%s, %d eventos, %d anomalías)",
            total_time, run_id, len(logs), int(logs["is_anomaly"].sum()),
        )

        return PipelineResult(
            logs=logs,
            semantic_backend=semantic_backend,
            saved_incidents=saved,
            profile=profile,
            stages=stages,
            statistical_backend=statistical_backend,
            semantic_scope=semantic_scope,
            persistence_error=persistence_error,
            silhouette_score=logs.attrs.get("silhouette_score", 0.0),
            davies_bouldin_index=logs.attrs.get("davies_bouldin_index", 0.0),
            run_id=run_id,
            log_source=log_source,
        )
