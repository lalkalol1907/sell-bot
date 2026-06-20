"""Hybrid product matching: fuzzy + optional semantic + variant attrs."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

import logging

from app.config import fuzzy_min_score, semantic_min_score
from app.handlers import metrics

logger = logging.getLogger(__name__)
from app.nlp.normalize import keyword_in_text, normalize_keyword, normalize_text
from app.nlp.variant_attrs import apply_variant_adjustment


@dataclass
class ProductGateResult:
    product_id: int
    title: str
    product_score: float
    fuzzy_score: float
    semantic_score: float
    matched_keywords: list[str]
    base_score: float = 0.0
    variant_multiplier: float = 1.0


def _keyword_fuzzy_score(normalized: str, keywords: list[str]) -> tuple[float, list[str]]:
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
        if ratio >= fuzzy_min_score():
            local_best = max(local_best, ratio)
            matched_kw.append(kw)

    return local_best, matched_kw


def _pick_better(
    current: ProductGateResult | None,
    candidate: ProductGateResult,
) -> ProductGateResult:
    if current is None:
        return candidate
    if candidate.product_score > current.product_score:
        return candidate
    if candidate.product_score == current.product_score:
        cur_kw = max(current.matched_keywords, key=len, default="")
        cand_kw = max(candidate.matched_keywords, key=len, default="")
        if len(cand_kw) > len(cur_kw):
            return candidate
    return current


def _fuzzy_match(normalized: str, raw_text: str, products: list[dict]) -> ProductGateResult | None:
    best: ProductGateResult | None = None

    for product in products:
        keywords = product.get("keywords") or [product.get("title", "")]
        base_score, matched_kw = _keyword_fuzzy_score(normalized, keywords)
        if base_score < fuzzy_min_score():
            continue

        adjusted = apply_variant_adjustment(base_score, raw_text, product)
        if adjusted < fuzzy_min_score():
            continue

        candidate = ProductGateResult(
            product_id=product["id"],
            title=product["title"],
            product_score=adjusted,
            fuzzy_score=adjusted,
            semantic_score=0.0,
            matched_keywords=matched_kw,
            base_score=base_score,
            variant_multiplier=adjusted / base_score if base_score else 1.0,
        )
        best = _pick_better(best, candidate)

    return best


def _semantic_match(
    normalized: str,
    raw_text: str,
    products: list[dict],
    seller_id: int,
) -> ProductGateResult | None:
    if not products:
        return None

    try:
        from app.embeddings.indexer import search_products

        hits = search_products(seller_id, normalized, products, limit=5)
        if not hits:
            return None

        min_sem = semantic_min_score()
        best: ProductGateResult | None = None
        for hit in hits:
            if hit.score < min_sem:
                continue
            product = next((p for p in products if p["id"] == hit.product_id), None)
            if product is None:
                continue

            adjusted = apply_variant_adjustment(hit.score, raw_text, product)
            if adjusted < min_sem:
                continue

            candidate = ProductGateResult(
                product_id=hit.product_id,
                title=product["title"],
                product_score=adjusted,
                fuzzy_score=0.0,
                semantic_score=adjusted,
                matched_keywords=product.get("keywords", [])[:1],
                base_score=hit.score,
                variant_multiplier=adjusted / hit.score if hit.score else 1.0,
            )
            best = _pick_better(best, candidate)

        return best
    except Exception as exc:
        logger.warning("semantic match failed seller=%s: %s", seller_id, exc)
        metrics.SEMANTIC_ERRORS.labels(stage="match").inc()
        return None


def match_product(
    text: str,
    products: list[dict],
    seller_id: int = 0,
) -> ProductGateResult | None:
    normalized = normalize_text(text)
    if not normalized or not products:
        return None

    fuzzy = _fuzzy_match(normalized, text, products)
    semantic = _semantic_match(normalized, text, products, seller_id) if seller_id else None

    if fuzzy is None and semantic is None:
        return None
    if fuzzy is None:
        return semantic
    if semantic is None:
        if seller_id:
            metrics.DEGRADED_TOTAL.inc()
        return fuzzy

    if semantic.product_score > fuzzy.product_score:
        semantic.fuzzy_score = fuzzy.fuzzy_score
        semantic.matched_keywords = fuzzy.matched_keywords or semantic.matched_keywords
        return semantic

    fuzzy.semantic_score = semantic.semantic_score
    return fuzzy
