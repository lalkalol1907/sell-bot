"""Shared pipeline context for a single message."""

from __future__ import annotations

from dataclasses import dataclass

from app.nlp.normalize import normalize_text


@dataclass(frozen=True)
class MessageContext:
    raw: str
    normalized: str


def build_message_context(raw: str, *, normalized: str | None = None) -> MessageContext:
    if normalized is None:
        normalized = normalize_text(raw)
    return MessageContext(raw=raw, normalized=normalized)
