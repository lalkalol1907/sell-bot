"""Process captured messages: spam filter → match → dedup → create lead."""

from __future__ import annotations

import logging

from app.config import REDIS_URL, semantic_min_score
from app.core_client import get_core_client
from app.dedup import DedupStore
from app.handlers import metrics
from app.handlers.process_result import ProcessResult
from app.pipeline.context import build_message_context
from app.pipeline.orchestrator import match_message
from app.spam_filter import check_spam

logger = logging.getLogger("matching")

dedup = DedupStore(REDIS_URL)


def process_message(
    seller_id: int,
    worker_id: int,
    chat_id: int,
    message_id: int,
    author_id: int,
    author_username: str,
    chat_title: str,
    raw_text: str,
) -> ProcessResult:
    ctx = build_message_context(raw_text)
    core = get_core_client()
    seller = core.get_seller(seller_id)
    sensitivity = seller.get("sensitivity", "precise")
    spam_phrases = seller.get("spam_phrases", [])

    spam_reason = check_spam(raw_text, spam_phrases, normalized=ctx.normalized)
    if spam_reason:
        metrics.SPAM_FILTERED.labels(reason=spam_reason).inc()
        metrics.MESSAGES_TOTAL.labels(result="spam_filtered").inc()
        logger.info("spam filtered seller=%s reason=%s", seller_id, spam_reason)
        return ProcessResult(matched=False, reason=f"spam_{spam_reason}")

    products = core.list_products(seller_id, active_only=True)

    result = match_message(
        raw_text,
        products,
        sensitivity,
        seller_id=seller_id,
        normalized=ctx.normalized,
    )
    if not result.matched or result.product is None:
        if result.reject_reason:
            metrics.GATE_REJECTED.labels(reason=result.reject_reason).inc()
        else:
            metrics.GATE_REJECTED.labels(reason="no_match").inc()
        if result.intent_class:
            metrics.INTENT_CLASS.labels(intent_class=result.intent_class).inc()
        metrics.MESSAGES_TOTAL.labels(result="no_match").inc()
        return ProcessResult(matched=False, reason=result.reject_reason or "no_match")

    threshold = semantic_min_score()
    if result.product.semantic_score >= threshold:
        metrics.SEMANTIC_HITS.inc()
    if result.intent_class:
        metrics.INTENT_CLASS.labels(intent_class=result.intent_class).inc()

    if not dedup.try_reserve(chat_id, author_id, result.product.product_id):
        logger.info("duplicate lead skipped chat=%s author=%s", chat_id, author_id)
        metrics.MESSAGES_TOTAL.labels(result="duplicate").inc()
        return ProcessResult(matched=False, reason="duplicate")

    lead_payload = {
        "seller_id": seller_id,
        "product_id": result.product.product_id,
        "worker_id": worker_id,
        "chat_id": chat_id,
        "message_id": message_id,
        "author_id": author_id,
        "author_username": author_username or "",
        "raw_text": raw_text,
        "matched_keywords": result.product.matched_keywords,
        "product_score": result.product_score,
        "intent_score": result.intent,
        "score": result.score,
        "level": result.level,
        "product_title": result.product.title,
        "chat_title": chat_title,
    }
    try:
        lead_id = core.create_lead(lead_payload)
    except Exception:
        dedup.release(chat_id, author_id, result.product.product_id)
        raise

    metrics.LEADS_CREATED.inc()
    metrics.MESSAGES_TOTAL.labels(result="lead").inc()
    logger.info("lead %d created for seller %d", lead_id, seller_id)

    return ProcessResult(
        matched=True,
        lead_id=lead_id,
        product_id=result.product.product_id,
        product_title=result.product.title,
        score=result.score,
        level=result.level,
    )
