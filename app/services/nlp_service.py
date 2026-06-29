import logging

from app.nlp.clustering_semantic import semantic_clusters
from app.nlp.embeddings import create_embeddings
from app.config.settings import HF_API_TOKEN, MAX_SEMANTIC_TEMPLATES

logger = logging.getLogger(__name__)


def _resolve_backend(backend: str) -> str | None:
    """Map user-facing backend choice to the internal force_backend value.

    - "auto"       → "remote" if HF_API_TOKEN is set, else None (local auto)
    - "distilbert" → "remote" if HF_API_TOKEN is set, else "distilbert"
    - "tfidf"      → "tfidf"
    """
    if backend == "tfidf":
        return "tfidf"
    if HF_API_TOKEN:
        return "remote"
    if backend == "distilbert":
        return "distilbert"
    return None  # auto, sin token → local auto-detect


def enrich_with_semantics(logs, backend: str = "auto"):
    df = logs.copy()
    force_backend = _resolve_backend(backend)
    logger.info(
        "NLP backend resuelto: %s (selección usuario: %s, token HF: %s)",
        force_backend,
        backend,
        "sí" if HF_API_TOKEN else "no",
    )

    # Si contamos con plantillas parseadas, clasterizamos sobre ellas (mucho más rápido y limpio)
    if "event_template" in df.columns:
        templates = (
            df["event_template"]
            .fillna("")
            .astype(str)
            .value_counts()
            .head(MAX_SEMANTIC_TEMPLATES)
            .index.tolist()
        )
        logger.info(
            "Procesando agrupamiento semántico sobre %d plantillas únicas.",
            len(templates),
        )

        embeddings, backend_val = create_embeddings(
            templates, force_backend=force_backend
        )
        labels = semantic_clusters(embeddings).values
        template_to_cluster = dict(zip(templates, labels))

        df["semantic_cluster"] = (
            df["event_template"].map(template_to_cluster).fillna(-1).astype(int)
        )
        df.attrs["semantic_backend"] = f"{backend_val}_templates"
        df.attrs["semantic_scope"] = f"{len(templates)} plantillas representativas"
        return df

    # Fallback si no hay Drain templates (procesar mensajes únicos)
    texts_series = df["clean_log"].fillna(df["raw_log"]).astype(str)
    unique_texts = texts_series.unique().tolist()
    logger.info(
        "Procesando agrupamiento semántico sobre %d mensajes únicos.", len(unique_texts)
    )

    embeddings, backend_val = create_embeddings(
        unique_texts, force_backend=force_backend
    )
    labels = semantic_clusters(embeddings).values
    text_to_cluster = dict(zip(unique_texts, labels))

    df["semantic_cluster"] = texts_series.map(text_to_cluster).fillna(-1).astype(int)
    df.attrs["semantic_backend"] = backend_val
    df.attrs["semantic_scope"] = "todos los eventos"
    return df
