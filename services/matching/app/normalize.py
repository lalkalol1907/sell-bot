"""Backward-compatible normalize re-exports."""

from app.nlp.normalize import normalize_text, normalize_text_legacy, normalize_text_v2, translit_expand

translit_pairs = translit_expand

__all__ = [
    "normalize_text",
    "normalize_text_legacy",
    "normalize_text_v2",
    "translit_pairs",
    "translit_expand",
]
