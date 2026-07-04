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
            error_msg = str(exc)
            if hasattr(exc, "response") and hasattr(exc.response, "text"):
                error_msg += f" | Detalle: {exc.response.text}"
            logger.warning("Error en DistilBERT remoto: %s. Realizando fallback a TF-IDF.", error_msg)
            # Fallback inmediato a TF-IDF
            embedder = SemanticEmbedder(force_backend="tfidf")
            return embedder.encode(texts), f"TF-IDF fallback (API Falló: {error_msg[:80]})"

    embedder = SemanticEmbedder(force_backend=force_backend)
    return embedder.encode(texts), embedder.backend
