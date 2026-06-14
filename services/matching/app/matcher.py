from dataclasses import dataclass

from rapidfuzz import fuzz

from app.intent import intent_score
from app.normalize import normalize_text


@dataclass
class ProductMatch:
    product_id: int
    title: str
    product_score: float
    matched_keywords: list[str]


@dataclass
class MatchResult:
    matched: bool
    level: str
    score: float
    product_score: float
    intent: float
    product: ProductMatch | None


def match_message(text: str, products: list[dict], sensitivity: str = "precise") -> MatchResult:
    normalized = normalize_text(text)
    if not normalized:
        return MatchResult(False, "", 0, 0, 0, None)

    best: ProductMatch | None = None
    best_score = 0.0

    for product in products:
        keywords = product.get("keywords") or [product.get("title", "")]
        matched_kw: list[str] = []
        local_best = 0.0

        for kw in keywords:
            kw_norm = normalize_text(kw)
            if not kw_norm:
                continue
            if kw_norm in normalized:
                local_best = max(local_best, 1.0)
                matched_kw.append(kw)
                continue
            ratio = fuzz.partial_ratio(kw_norm, normalized) / 100.0
            if ratio >= 0.85:
                local_best = max(local_best, ratio)
                matched_kw.append(kw)

        if local_best > best_score:
            best_score = local_best
            best = ProductMatch(
                product_id=product["id"],
                title=product["title"],
                product_score=local_best,
                matched_keywords=matched_kw,
            )

    if best is None or best_score < 0.85:
        return MatchResult(False, "", 0, 0, 0, None)

    intent = intent_score(normalized)
    if intent < 0:
        return MatchResult(False, "", 0, best_score, intent, best)

    combined = best_score * 0.6 + max(intent, 0) * 0.4
    if intent >= 0.8:
        level = "confirmed"
    elif intent >= 0.4 or sensitivity == "aggressive":
        level = "probable"
    else:
        return MatchResult(False, "", combined, best_score, intent, best)

    return MatchResult(True, level, combined, best_score, intent, best)
