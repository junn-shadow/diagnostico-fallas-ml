import logging
import time
from typing import List

import numpy as np
from huggingface_hub import InferenceClient

from app.config.settings import HF_API_TOKEN, DISTILBERT_MODEL_NAME

logger = logging.getLogger(__name__)


class RemoteSemanticEmbedder:
    """Client for Hugging Face Inference API (feature-extraction pipeline).
    Uses the official huggingface_hub library for robust connectivity.
    Falls back gracefully if the token is missing or the API fails.
    """

    def __init__(self, model_name: str = DISTILBERT_MODEL_NAME, timeout: int = 35):
        self.model_name = model_name
        self.timeout = timeout
        self.backend = "distilbert_remote"
        
        # Initialize official InferenceClient
        if HF_API_TOKEN:
            self.client = InferenceClient(api_key=HF_API_TOKEN, timeout=self.timeout)
        else:
            self.client = None

    @staticmethod
    def _pool_token_embeddings(token_embeddings: list) -> np.ndarray:
        """Mean-pool the per-token vectors returned by HF into a single vector."""
        arr = np.array(token_embeddings, dtype=np.float32)
        if arr.ndim == 2:
            return arr.mean(axis=0)
        return arr

    def encode(self, texts: List[str], batch_size: int = 50) -> np.ndarray:
        if not self.client:
            raise RuntimeError(
                "HF_API_TOKEN no está configurado. "
                "Define la variable de entorno HF_API_TOKEN con tu token de Hugging Face."
            )
        if not texts:
            return np.empty((0, 0))

        all_embeddings: List[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            logger.info(
                "HF API: enviando lote %d-%d de %d textos con InferenceClient",
                start,
                start + len(batch),
                len(texts),
            )
            
            # Retry logic with the official client
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    # The official client automatically routes correctly
                    result = self.client.feature_extraction(
                        text=batch, 
                        model=self.model_name
                    )
                    
                    # Ensure numpy array parsing
                    batch_vecs = []
                    for item in result:
                        if isinstance(item, (list, tuple)) and isinstance(item[0], (list, tuple)):
                            batch_vecs.append(self._pool_token_embeddings(item))
                        else:
                            batch_vecs.append(np.array(item, dtype=np.float32))
                    
                    all_embeddings.extend(batch_vecs)
                    break  # Success, exit retry loop
                    
                except Exception as exc:
                    if attempt < max_retries:
                        wait = 2 ** attempt
                        logger.warning("Error HF InferenceClient: %s. Reintentando en %ds...", str(exc), wait)
                        time.sleep(wait)
                    else:
                        logger.error("Error definitivo HF InferenceClient tras %d intentos: %s", max_retries + 1, str(exc))
                        raise

        if not all_embeddings:
            return np.empty((0, 0))
            
        return np.vstack(all_embeddings)
