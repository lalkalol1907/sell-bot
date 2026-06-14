import json
import logging
import os
import threading
from concurrent import futures

import grpc
from fastapi import FastAPI

from app.core_client import get_core_client
from app.dedup import DedupStore
from app.matcher import match_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching")

app = FastAPI(title="sellbot-matching")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50052"))

dedup = DedupStore(REDIS_URL)


@app.get("/health")
def health():
    return {"status": "ok"}


def _publish_lead_created(payload: dict) -> None:
    import nats

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            nc = nats.connect(NATS_URL)
            nc.publish("lead.created", json.dumps(payload).encode())
            nc.flush()
            nc.close()
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("nats publish attempt %d failed: %s", attempt, exc)
    raise RuntimeError("nats publish failed after 3 attempts") from last_exc


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
    products = core.list_products(seller_id, active_only=True)

    result = match_message(raw_text, products, sensitivity)
    if not result.matched or result.product is None:
        return {"matched": False}

    if not dedup.try_reserve(chat_id, author_id, result.product.product_id):
        logger.info("duplicate lead skipped chat=%s author=%s", chat_id, author_id)
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
    }
    try:
        lead_id = core.create_lead(lead_payload)
    except Exception:
        dedup.release(chat_id, author_id, result.product.product_id)
        raise

    event = {
        **lead_payload,
        "lead_id": lead_id,
        "tg_user_id": seller["tg_user_id"],
        "product_title": result.product.title,
        "chat_title": chat_title,
    }
    try:
        _publish_lead_created(event)
    except Exception as exc:
        logger.error("lead %d created but notification failed: %s", lead_id, exc)
        return {
            "matched": True,
            "lead_id": lead_id,
            "product_id": result.product.product_id,
            "product_title": result.product.title,
            "score": result.score,
            "level": result.level,
            "notify_failed": True,
        }

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
