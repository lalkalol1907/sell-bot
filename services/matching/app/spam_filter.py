"""Pre-match spam filters: message length and learned phrases."""

from __future__ import annotations

import os

from app.nlp.normalize import normalize_text

MIN_MESSAGE_CHARS = int(os.getenv("MIN_MESSAGE_CHARS", "8"))
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "2000"))


def is_spam_by_length(text: str) -> bool:
    length = len(text.strip())
    return length < MIN_MESSAGE_CHARS or length > MAX_MESSAGE_CHARS


def matches_learned_spam(normalized: str, spam_phrases: list[str]) -> bool:
    if not normalized or not spam_phrases:
        return False
    for phrase in spam_phrases:
        p = phrase.strip().lower()
        if p and p in normalized:
            return True
    return False


def check_spam(
    raw_text: str,
    spam_phrases: list[str],
    *,
    normalized: str | None = None,
) -> str | None:
    """Return rejection reason or None if message passes filters."""
    if is_spam_by_length(raw_text):
        return "length"
    if normalized is None:
        normalized = normalize_text(raw_text)
    if matches_learned_spam(normalized, spam_phrases):
        return "learned"
    return None
