"""gRPC server for direct ProcessMessage calls."""

from __future__ import annotations

import logging
import os
import threading
from concurrent import futures

import grpc

from app.handlers.message_processor import process_message

logger = logging.getLogger("matching")

GRPC_PORT = int(os.getenv("GRPC_PORT", "50052"))


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
                matched=result.matched,
                lead_id=result.lead_id,
                product_id=result.product_id,
                product_title=result.product_title,
                score=result.score,
                level=result.level,
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
