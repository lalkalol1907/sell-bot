import json
import logging
import os
import threading
from concurrent import futures

import grpc
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from app.core_client import get_core_client
from app.dedup import DedupStore
from app.config import NLP_V2_ENABLED
from app.matcher import match_message
from app.models_runtime import current_version
from app.spam_filter import check_spam

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching")

app = FastAPI(title="sellbot-matching")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50052"))

dedup = DedupStore(REDIS_URL)

MESSAGES_TOTAL = Counter("matching_messages_total", "Messages processed", ["result"])
SPAM_FILTERED = Counter("matching_spam_filtered_total", "Messages filtered as spam", ["reason"])
LEADS_CREATED = Counter("matching_leads_created_total", "Leads created")
SEMANTIC_HITS = Counter("matching_semantic_hits_total", "Semantic product gate hits")
INTENT_CLASS = Counter("matching_intent_class_total", "Intent class distribution", ["intent_class"])
GATE_REJECTED = Counter("matching_product_gate_rejected_total", "Product gate rejections", ["reason"])


@app.get("/health")
def health():
    return {"status": "ok", "models_version": current_version()}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def process_message(
    seller_id: int,
    worker_id: int,
    chat_id: int,
    message_id: int,
    author_id: int,
    author_username: str,
    chat_title: str,
    raw_text: str,
) -> dict:
    core = get_core_client()
    seller = core.get_seller(seller_id)
    sensitivity = seller.get("sensitivity", "precise")
    spam_phrases = seller.get("spam_phrases", [])

    spam_reason = check_spam(raw_text, spam_phrases)
    if spam_reason:
        SPAM_FILTERED.labels(reason=spam_reason).inc()
        MESSAGES_TOTAL.labels(result="spam_filtered").inc()
        logger.info("spam filtered seller=%s reason=%s", seller_id, spam_reason)
        return {"matched": False, "reason": f"spam_{spam_reason}"}

    products = core.list_products(seller_id, active_only=True)

    result = match_message(raw_text, products, sensitivity, seller_id=seller_id)
    if not result.matched or result.product is None:
        if result.reject_reason:
            GATE_REJECTED.labels(reason=result.reject_reason).inc()
        else:
            GATE_REJECTED.labels(reason="no_match").inc()
        if result.intent_class:
            INTENT_CLASS.labels(intent_class=result.intent_class).inc()
        MESSAGES_TOTAL.labels(result="no_match").inc()
        return {"matched": False, "reason": result.reject_reason or "no_match"}

    if NLP_V2_ENABLED and result.product.semantic_score >= 0.72:
        SEMANTIC_HITS.inc()
    if result.intent_class:
        INTENT_CLASS.labels(intent_class=result.intent_class).inc()

    if not dedup.try_reserve(chat_id, author_id, result.product.product_id):
        logger.info("duplicate lead skipped chat=%s author=%s", chat_id, author_id)
        MESSAGES_TOTAL.labels(result="duplicate").inc()
        return {"matched": False, "reason": "duplicate"}

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

    LEADS_CREATED.inc()
    MESSAGES_TOTAL.labels(result="lead").inc()
    logger.info("lead %d created for seller %d", lead_id, seller_id)

    return {
        "matched": True,
        "lead_id": lead_id,
        "product_id": result.product.product_id,
        "product_title": result.product.title,
        "score": result.score,
        "level": result.level,
    }


def _build_grpc_server():
    from app.generated import matching_pb2, matching_pb2_grpc

    class MatchingServicer(matching_pb2_grpc.MatchingServiceServicer):
        def ProcessMessage(self, request, context):
            result = process_message(
                seller_id=request.seller_id,
                worker_id=request.worker_id,
                chat_id=request.chat_id,
                message_id=request.message_id,
                author_id=request.author_id,
                author_username=request.author_username,
                chat_title=request.chat_title,
                raw_text=request.raw_text,
            )
            return matching_pb2.ProcessMessageResponse(
                matched=result.get("matched", False),
                lead_id=result.get("lead_id", 0),
                product_id=result.get("product_id", 0),
                product_title=result.get("product_title", ""),
                score=result.get("score", 0.0),
                level=result.get("level", ""),
            )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    matching_pb2_grpc.add_MatchingServiceServicer_to_server(MatchingServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    return server


def serve_grpc():
    server = _build_grpc_server()
    server.start()
    logger.info("gRPC server listening on %s", GRPC_PORT)
    server.wait_for_termination()


def start():
    thread = threading.Thread(target=serve_grpc, daemon=True)
    thread.start()
