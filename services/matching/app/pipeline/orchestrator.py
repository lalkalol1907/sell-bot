"""Message matching pipeline: normalize → product gate → intent → scoring."""

from __future__ import annotations

from dataclasses import dataclass

from app.nlp.intent_classifier import classify_intent
from app.nlp.product_gate import ProductGateResult, match_product
from app.nlp.scoring import compute_level
from app.pipeline.context import build_message_context


@dataclass
class MatchResult:
    matched: bool
    level: str
    score: float
    product_score: float
    intent: float
    product: ProductGateResult | None
    intent_class: str = ""
    reject_reason: str = ""


def match_message(
    text: str,
    products: list[dict],
    sensitivity: str = "precise",
    seller_id: int = 0,
    *,
    normalized: str | None = None,
) -> MatchResult:
    ctx = build_message_context(text, normalized=normalized)
    if not ctx.normalized:
        return MatchResult(False, "", 0, 0, 0, None, reject_reason="empty")

    intent = classify_intent(ctx.raw, normalized=ctx.normalized)
    if intent.score < 0:
        return MatchResult(
            False, "", 0, 0, intent.score, None,
            intent_class=intent.label, reject_reason="sell_intent",
        )

    gate = match_product(
        ctx.raw,
        products,
        seller_id=seller_id,
        normalized=ctx.normalized,
    )
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

    if not score_result.matched:
        return MatchResult(
            False,
            "",
            score_result.combined,
            gate.product_score,
            intent.score,
            gate,
            intent_class=intent.label,
            reject_reason=score_result.reject_reason,
        )

    return MatchResult(
        True,
        score_result.level,
        score_result.combined,
        gate.product_score,
        intent.score,
        gate,
        intent_class=intent.label,
    )
