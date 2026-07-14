from dataclasses import dataclass

from app.config.settings import DISTILBERT_MODEL_NAME, HF_API_TOKEN


@dataclass
class ModelStatus:
    model_name: str
    available_locally: bool
    available_remote: bool
    backend: str
    detail: str


import streamlit as st

@st.cache_data(show_spinner=False, ttl=300)
def check_distilbert_status(model_name: str = DISTILBERT_MODEL_NAME) -> ModelStatus:
    """Check DistilBERT availability: remote API (preferred) or local cache."""

    # Check remote availability first
    if HF_API_TOKEN:
        return ModelStatus(
            model_name=model_name,
            available_locally=False,
            available_remote=True,
            backend="distilbert_remote",
            detail="Conectado a Hugging Face Inference API (remoto).",
        )

    # Check local availability
    try:
        import os

        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        import torch

        torch.set_num_threads(1)
        from transformers import AutoModel, AutoTokenizer

        AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        AutoModel.from_pretrained(model_name, local_files_only=True)
        return ModelStatus(
            model_name=model_name,
            available_locally=True,
            available_remote=False,
            backend="distilbert",
            detail="Modelo disponible en cache local.",
        )
    except Exception as exc:
        return ModelStatus(
            model_name=model_name,
            available_locally=False,
            available_remote=False,
            backend="tfidf_fallback",
            detail=f"Sin token HF_API_TOKEN y modelo no disponible localmente: {exc.__class__.__name__}. Usando TF-IDF.",
        )
