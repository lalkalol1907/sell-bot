"""Message matching orchestrator (legacy + NLP v2)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import FUZZY_MIN_SCORE, NLP_V2_ENABLED, SEMANTIC_MIN_SCORE


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


def _match_legacy(text: str, products: list[dict], sensitivity: str) -> MatchResult:
    from rapidfuzz import fuzz

    from app.nlp.intent_classifier import classify_intent
    from app.nlp.normalize import keyword_in_text, normalize_keyword, normalize_text
    from app.nlp.variant_attrs import apply_variant_adjustment

    normalized = normalize_text(text)
    if not normalized:
        return MatchResult(False, "", 0, 0, 0, None, reject_reason="empty")

    intent = classify_intent(normalized)
    if intent.score < 0:
        return MatchResult(
            False, "", 0, 0, intent.score, None,
            intent_class=intent.label, reject_reason="sell_intent",
        )

    best: ProductMatch | None = None
    best_score = 0.0

    for product in products:
        keywords = product.get("keywords") or [product.get("title", "")]
        matched_kw: list[str] = []
        local_best = 0.0

        for kw in keywords:
            kw_norm = normalize_keyword(kw)
            if not kw_norm:
                continue
            if keyword_in_text(kw, normalized):
                local_best = max(local_best, 1.0)
                matched_kw.append(kw)
                continue
            ratio = (
                max(
                    fuzz.partial_ratio(kw_norm, normalized),
                    fuzz.token_set_ratio(kw_norm, normalized),
                    fuzz.WRatio(kw_norm, normalized),
                )
                / 100.0
            )
            if ratio >= 0.85:
                local_best = max(local_best, ratio)
                matched_kw.append(kw)

        adjusted = apply_variant_adjustment(local_best, text, product) if local_best >= 0.85 else 0.0
        if adjusted < 0.85:
            continue

        if adjusted > best_score:
            should_update = True
        elif (
            adjusted == best_score
            and best is not None
            and matched_kw
            and len(max(matched_kw, key=len)) > len(max(best.matched_keywords, key=len, default=""))
        ):
            should_update = True
        else:
            should_update = False

        if should_update:
            best_score = adjusted
            best = ProductMatch(
                product_id=product["id"],
                title=product["title"],
                product_score=adjusted,
                matched_keywords=matched_kw,
                fuzzy_score=adjusted,
            )

    if best is None or best_score < 0.85:
        return MatchResult(False, "", 0, 0, intent.score, None, reject_reason="no_product")

    if intent.label == "discussion" and sensitivity == "precise":
        return MatchResult(
            False, "", best_score * 0.6, best_score, intent.score, best,
            intent_class=intent.label, reject_reason="discussion",
        )

    combined = best_score * 0.6 + max(intent.score, 0) * 0.4
    if intent.score >= 0.8:
        level = "confirmed"
    elif sensitivity in ("aggressive", "balanced"):
        if intent.label in ("buy", "discussion") or intent.score >= 0.4:
            level = "probable"
        else:
            return MatchResult(
                False, "", combined, best_score, intent.score, best,
                intent_class=intent.label, reject_reason="low_intent",
            )
    else:
        return MatchResult(
            False, "", combined, best_score, intent.score, best,
            intent_class=intent.label, reject_reason="low_intent",
        )

    return MatchResult(True, level, combined, best_score, intent.score, best, intent_class=intent.label)


def _match_v2(text: str, products: list[dict], sensitivity: str, seller_id: int) -> MatchResult:
    from app.nlp.intent_classifier import classify_intent
    from app.nlp.normalize import normalize_text
    from app.nlp.product_gate import match_product
    from app.nlp.scoring import compute_level

    normalized = normalize_text(text)
    if not normalized:
        return MatchResult(False, "", 0, 0, 0, None, reject_reason="empty")

    intent = classify_intent(normalized)
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


def match_message(
    text: str,
    products: list[dict],
    sensitivity: str = "precise",
    seller_id: int = 0,
) -> MatchResult:
    if NLP_V2_ENABLED:
        return _match_v2(text, products, sensitivity, seller_id)
    return _match_legacy(text, products, sensitivity)


def product_passes_threshold(fuzzy_score: float, semantic_score: float) -> bool:
    return fuzzy_score >= FUZZY_MIN_SCORE or semantic_score >= SEMANTIC_MIN_SCORE
