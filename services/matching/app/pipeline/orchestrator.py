"""Message matching pipeline: normalize → product gate → intent → scoring."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import fuzzy_min_score, semantic_min_score
from app.nlp.intent_classifier import classify_intent
from app.nlp.normalize import normalize_text
from app.nlp.product_gate import match_product
from app.nlp.scoring import compute_level


@dataclass
class ProductMatch:
    product_id: int
    title: str
    product_score: float
    matched_keywords: list[str]
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0


@dataclass
class MatchResult:
    matched: bool
    level: str
    score: float
    product_score: float
    intent: float
    product: ProductMatch | None
    intent_class: str = ""
    reject_reason: str = ""


def match_message(
    text: str,
    products: list[dict],
    sensitivity: str = "precise",
    seller_id: int = 0,
) -> MatchResult:
    normalized = normalize_text(text)
    if not normalized:
        return MatchResult(False, "", 0, 0, 0, None, reject_reason="empty")

    intent = classify_intent(text)
    if intent.score < 0:
        return MatchResult(
            False, "", 0, 0, intent.score, None,
            intent_class=intent.label, reject_reason="sell_intent",
        )

    gate = match_product(text, products, seller_id=seller_id)
    if gate is None:
        return MatchResult(
            False, "", 0, 0, intent.score, None,
            intent_class=intent.label, reject_reason="no_product",
        )

    score_result = compute_level(
        gate.product_score,
        intent,
        sensitivity,
        fuzzy_score=gate.fuzzy_score,
        semantic_score=gate.semantic_score,
    )

    product = ProductMatch(
        product_id=gate.product_id,
        title=gate.title,
        product_score=gate.product_score,
        matched_keywords=gate.matched_keywords,
        fuzzy_score=gate.fuzzy_score,
        semantic_score=gate.semantic_score,
    )

    if not score_result.matched:
        return MatchResult(
            False,
            "",
            score_result.combined,
            gate.product_score,
            intent.score,
            product,
            intent_class=intent.label,
            reject_reason=score_result.reject_reason,
        )

    return MatchResult(
        True,
        score_result.level,
        score_result.combined,
        gate.product_score,
        intent.score,
        product,
        intent_class=intent.label,
    )


def product_passes_threshold(fuzzy_score: float, semantic_score: float) -> bool:
    return fuzzy_score >= fuzzy_min_score() or semantic_score >= semantic_min_score()
