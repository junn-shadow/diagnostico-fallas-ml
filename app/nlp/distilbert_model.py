import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config.settings import DISTILBERT_MODEL_NAME

logger = logging.getLogger(__name__)


class SemanticEmbedder:
    """DistilBERT embedder with a deterministic TF-IDF fallback for offline demos."""

    _shared_tokenizer = None
    _shared_model = None
    _shared_backend = None
    _loaded = False

    def __init__(
        self, model_name: str = DISTILBERT_MODEL_NAME, force_backend: str = None
    ):
        self.model_name = model_name
        self.vectorizer = TfidfVectorizer(max_features=384, ngram_range=(1, 2))
        self.tokenizer = None
        self.model = None

        if not SemanticEmbedder._loaded:
            try:
                import os

                os.environ["TOKENIZERS_PARALLELISM"] = "false"
                import torch

                torch.set_num_threads(1)
                from transformers import AutoModel, AutoTokenizer

                SemanticEmbedder._shared_tokenizer = AutoTokenizer.from_pretrained(
                    model_name, local_files_only=True
                )
                SemanticEmbedder._shared_model = AutoModel.from_pretrained(
                    model_name, local_files_only=True
                )
                SemanticEmbedder._shared_model.eval()
                SemanticEmbedder._shared_backend = "distilbert"
            except Exception:
                SemanticEmbedder._shared_backend = "tfidf"
            SemanticEmbedder._loaded = True

        self.tokenizer = SemanticEmbedder._shared_tokenizer
        self.model = SemanticEmbedder._shared_model

        if force_backend in ("distilbert", "tfidf"):
            self.backend = force_backend
        else:
            self.backend = SemanticEmbedder._shared_backend

        logger.info("SemanticEmbedder inicializado con backend: %s", self.backend)

        if self.backend == "distilbert":
            import torch

            self.torch = torch
        else:
            self.torch = None

    def encode(self, texts: list[str], batch_size: int = 32):
        if not texts:
            return np.empty((0, 0))

        # Proteger contra textos vacíos que rompen el tokenizer
        safe_texts = [str(t) if str(t).strip() else "[EMPTY]" for t in texts]

        if self.backend == "distilbert":
            batches = []
            for start in range(0, len(safe_texts), batch_size):
                chunk = safe_texts[start : start + batch_size]
                encoded = self.tokenizer(
                    chunk, padding=True, truncation=True, return_tensors="pt"
                )
                with self.torch.no_grad():
                    output = self.model(**encoded)
                attention = encoded["attention_mask"].unsqueeze(-1)
                pooled = (output.last_hidden_state * attention).sum(1) / attention.sum(
                    1
                ).clamp(min=1)
                batches.append(pooled.numpy())
            return np.vstack(batches)

        if hasattr(self.vectorizer, "vocabulary_"):
            return self.vectorizer.transform(safe_texts)
        return self.vectorizer.fit_transform(safe_texts)
