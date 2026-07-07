from __future__ import annotations

from threading import Lock
from typing import Any

_MODELS: dict[str, Any] = {}
_LOCK = Lock()


def get_sentence_transformer(model_name: str):
    """Load each SentenceTransformer model once, lazily.

    Importing sentence_transformers pulls in ML stacks, so keep it out of the
    backend import path and only load the model when embeddings are required.
    """
    model = _MODELS.get(model_name)
    if model is not None:
        return model

    with _LOCK:
        model = _MODELS.get(model_name)
        if model is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_name, local_files_only=True)
            _MODELS[model_name] = model
        return model

