"""Scoring and level assignment."""

from __future__ import annotations

from dataclasses import dataclass

from app.nlp.intent_classifier import IntentResult


@dataclass
class ScoreResult:
    combined: float
    level: str
    matched: bool
    reject_reason: str = ""


def compute_level(
    product_score: float,
    intent: IntentResult,
    sensitivity: str,
    *,
    fuzzy_score: float = 0.0,
    semantic_score: float = 0.0,
    product_threshold: float = 0.85,
) -> ScoreResult:
    from app.config import FUZZY_MIN_SCORE, SEMANTIC_MIN_SCORE

    if intent.score < 0:
        return ScoreResult(0, "", False, "sell_intent")

    passes_fuzzy = fuzzy_score >= FUZZY_MIN_SCORE
    passes_semantic = semantic_score >= SEMANTIC_MIN_SCORE
    if not passes_fuzzy and not passes_semantic:
        if product_score < product_threshold:
            return ScoreResult(0, "", False, "no_product")

    combined = product_score * 0.55 + max(intent.score, 0) * 0.45

    if intent.label == "discussion" and sensitivity == "precise":
        return ScoreResult(combined, "", False, "discussion")

    if intent.score >= 0.8 or (intent.label == "buy" and intent.score >= 0.55):
        if intent.score >= 0.8:
            return ScoreResult(combined, "confirmed", True)
        if sensitivity in ("aggressive", "balanced"):
            return ScoreResult(combined, "probable", True)
        return ScoreResult(combined, "", False, "low_intent")

    if intent.score >= 0.4 or sensitivity in ("aggressive", "balanced"):
        return ScoreResult(combined, "probable", True)

    if intent.label == "discussion":
        return ScoreResult(combined, "", False, "discussion")

    return ScoreResult(combined, "", False, "low_intent")
