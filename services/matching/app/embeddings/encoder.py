"""Embedding encoder (sentence-transformers with lazy load)."""

from __future__ import annotations

from functools import lru_cache

_encoder = None


@lru_cache(maxsize=1)
def _load_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder

    from app.config import EMBEDDING_MODEL

    try:
        from sentence_transformers import SentenceTransformer

        _encoder = SentenceTransformer(EMBEDDING_MODEL)
        return _encoder
    except Exception as exc:
        raise RuntimeError(f"Failed to load embedding model: {exc}") from exc


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = _load_encoder()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def encode_text(text: str) -> list[float]:
    return encode_texts([text])[0]


def is_encoder_available() -> bool:
    try:
        _load_encoder()
        return True
    except Exception:
        return False
