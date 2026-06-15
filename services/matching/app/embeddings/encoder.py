"""Embedding encoder (fastembed ONNX, lazy load)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_encoder = None

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_EMBEDDING_SUBDIR = Path("embedding") / "paraphrase-multilingual-MiniLM-L12-v2"


def _resolve_embedding_model_dir() -> Path | None:
    explicit = os.getenv("EMBEDDING_MODEL_DIR", "").strip()
    if explicit:
        path = Path(explicit)
        if path.is_dir():
            return path
        logger.warning("EMBEDDING_MODEL_DIR not found: %s", path)
        return None

    local_root = os.getenv("MODELS_LOCAL_DIR", "").strip()
    if local_root:
        candidate = Path(local_root) / DEFAULT_EMBEDDING_SUBDIR
        if candidate.is_dir():
            return candidate

    from app.paths import models_dir

    candidate = models_dir() / DEFAULT_EMBEDDING_SUBDIR
    if candidate.is_dir():
        return candidate
    return None


@lru_cache(maxsize=1)
def _load_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder

    from app.config import EMBEDDING_MODEL_NAME

    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise RuntimeError("fastembed is not installed") from exc

    model_dir = _resolve_embedding_model_dir()
    kwargs: dict = {"model_name": EMBEDDING_MODEL_NAME}
    if model_dir is not None:
        kwargs["specific_model_path"] = str(model_dir)
        logger.info("Loading embedding model from %s", model_dir)
    else:
        logger.info("Loading embedding model from hub: %s", EMBEDDING_MODEL_NAME)

    _encoder = TextEmbedding(**kwargs)
    return _encoder


def _normalize_vectors(vectors: list[np.ndarray]) -> list[list[float]]:
    result: list[list[float]] = []
    for vector in vectors:
        arr = np.asarray(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        result.append(arr.tolist())
    return result


def encode_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _load_encoder()
    vectors = list(model.embed(texts, batch_size=32))
    return _normalize_vectors(vectors)


def encode_text(text: str) -> list[float]:
    return encode_texts([text])[0]


def is_encoder_available() -> bool:
    try:
        _load_encoder()
        return True
    except Exception:
        return False


def reset_encoder_cache() -> None:
    global _encoder
    _encoder = None
    _load_encoder.cache_clear()
