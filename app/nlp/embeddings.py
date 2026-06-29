import logging

from app.nlp.distilbert_model import SemanticEmbedder
from app.nlp.remote_distilbert import RemoteSemanticEmbedder
from app.config.settings import HF_API_TOKEN

logger = logging.getLogger(__name__)


def create_embeddings(texts: list[str], force_backend: str = None):
    """Create embeddings using DistilBERT (remote API or local) with TF-IDF fallback.

    If using the remote backend and a network/API failure occurs, it gracefully
    falls back to the local SemanticEmbedder.
    """
    if force_backend == "remote":
        logger.info("Intentando usar DistilBERT remoto (HF Inference API)...")
        try:
            embedder = RemoteSemanticEmbedder()
            embs = embedder.encode(texts)
            logger.info("Embeddings generados exitosamente via HF Inference API.")
            return embs, embedder.backend
        except Exception as exc:
            logger.warning(
                "Error en DistilBERT remoto [%s]: %s. Realizando fallback a TF-IDF.",
                exc.__class__.__name__,
                exc,
            )
            # Fallback inmediato a TF-IDF para evitar bloqueos y lentitud de CPU local
            force_backend = "tfidf"

    embedder = SemanticEmbedder(force_backend=force_backend)
    return embedder.encode(texts), embedder.backend
