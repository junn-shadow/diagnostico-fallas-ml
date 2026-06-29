import logging
from app.correlation.recommendation_engine import infer_semantic_diagnostics
from app.config.settings import HF_API_TOKEN

logger = logging.getLogger(__name__)


def _resolve_alert_backend(nlp_backend: str) -> str | None:
    """Same logic as nlp_service: prefer remote when token is available."""
    if nlp_backend == "tfidf":
        return "tfidf"
    if HF_API_TOKEN:
        return "remote"
    if nlp_backend == "distilbert":
        return "distilbert"
    return None


def generate_alerts(logs, nlp_backend: str = "auto"):
    """
    Genera alertas enriqueciendo el DataFrame de logs con causas raíces y
    recomendaciones utilizando el motor de inferencia semántica.
    Optimizado para procesar semánticamente solo anomalías y errores/advertencias.
    Realiza diagnósticos agrupados por plantillas de error únicas para un rendimiento óptimo.
    """
    df = logs.copy()

    # Inicializar columnas con valores por defecto
    df["root_cause"] = "Comportamiento normal"
    df["recommendation"] = "No requiere accion"
    df["severity_label"] = df["level"].replace({"WARN": "WARNING"})

    # Identificar filas que requieren diagnóstico (anomalías, advertencias o errores)
    mask = df["is_anomaly"] | df["level"].isin(
        ["WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]
    )

    if mask.any():
        # Si contamos con plantillas, las usamos de clave para evitar duplicados y variaciones dinámicas
        if "event_template" in df.columns:
            source_series = df.loc[mask, "event_template"]
        else:
            source_series = df.loc[mask, "clean_log"].fillna(df.loc[mask, "raw_log"])

        # Obtener valores únicos de plantillas/mensajes a diagnosticar
        unique_alerts = source_series.fillna("").astype(str).unique().tolist()
        logger.info(
            "Diagnosticando semánticamente %d alertas/plantillas únicas.",
            len(unique_alerts),
        )

        # Ejecutar la inferencia semántica sobre el subconjunto único reducido
        force_backend = _resolve_alert_backend(nlp_backend)
        root_causes, recommendations = infer_semantic_diagnostics(
            unique_alerts, force_backend=force_backend
        )

        # Mapear resultados de regreso
        diag_map = {}
        for alert_text, cause, rec in zip(unique_alerts, root_causes, recommendations):
            diag_map[alert_text] = (cause, rec)

        mapped_results = source_series.fillna("").astype(str).map(diag_map)
        df.loc[mask, "root_cause"] = mapped_results.apply(
            lambda x: x[0] if isinstance(x, tuple) else "Comportamiento normal"
        )
        df.loc[mask, "recommendation"] = mapped_results.apply(
            lambda x: x[1] if isinstance(x, tuple) else "No requiere accion"
        )

    return df
