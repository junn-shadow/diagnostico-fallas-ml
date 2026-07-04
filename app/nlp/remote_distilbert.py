import logging
import numpy as np
import requests
import time
from typing import List

from app.config.settings import HF_API_TOKEN, DISTILBERT_MODEL_NAME

logger = logging.getLogger(__name__)


class RemoteSemanticEmbedder:
    """Client for Hugging Face Inference API (feature-extraction pipeline).
    Sends texts to the HF API and returns dense NumPy embeddings.
    Falls back gracefully if the token is missing or the API fails.
    """

    def __init__(self, model_name: str = DISTILBERT_MODEL_NAME, timeout: int = 35):
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = (
            {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
        )
        self.timeout = timeout
        self.backend = "distilbert_remote"

    # ------------------------------------------------------------------
    def _call_api(self, texts: List[str]) -> list:
        """POST a batch of texts and return the raw JSON response with retries."""
        payload = {
            "inputs": texts,
            "options": {"wait_for_model": True, "use_cache": True},
        }
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            t0 = time.perf_counter()
            try:
                resp = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                latency = time.perf_counter() - t0
                logger.debug("HF API request exitoso (status=%d, latency=%.2fs)", resp.status_code, latency)
                return resp.json()
            except Exception as exc:
                latency = time.perf_counter() - t0
                status_code = getattr(exc.response, "status_code", "N/A") if hasattr(exc, "response") else "N/A"
                if attempt < max_retries:
                    wait = 2 ** attempt  # 1s, 2s
                    logger.warning("Error HF API (status=%s, latency=%.2fs): %s. Reintentando en %ds...", status_code, latency, exc, wait)
                    time.sleep(wait)
                else:
                    logger.error("Error definitivo HF API tras %d intentos (status=%s): %s", max_retries + 1, status_code, exc)
                    raise

    # ------------------------------------------------------------------
    @staticmethod
    def _pool_token_embeddings(token_embeddings: list) -> np.ndarray:
        """Mean-pool the per-token vectors returned by HF into a single vector."""
        arr = np.array(token_embeddings, dtype=np.float32)
        if arr.ndim == 2:
            return arr.mean(axis=0)
        # Some models return 1-D directly
        return arr

    # ------------------------------------------------------------------
    def encode(self, texts: List[str], batch_size: int = 50) -> np.ndarray:
        if not HF_API_TOKEN:
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
                "HF API: enviando lote %d-%d de %d textos",
                start,
                start + len(batch),
                len(texts),
            )
            try:
                result = self._call_api(batch)
                # result is a list (one entry per input).
                # Each entry is either:
                #   - a list of floats (sentence embedding)
                #   - a list of lists of floats (token embeddings → we mean-pool)
                batch_vecs = []
                for item in result:
                    if isinstance(item[0], list):
                        batch_vecs.append(self._pool_token_embeddings(item))
                    else:
                        batch_vecs.append(np.array(item, dtype=np.float32))
                all_embeddings.append(np.vstack(batch_vecs))
            except Exception as exc:
                logger.error("Error en HF API lote %d: %s", start, exc)
                raise

        return np.vstack(all_embeddings)
