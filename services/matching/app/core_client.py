"""gRPC client for Core (catalog + leads)."""

from __future__ import annotations

import logging
import os

import grpc

logger = logging.getLogger(__name__)

CORE_GRPC_ADDR = os.getenv("CORE_GRPC_ADDR", "core:50051")


def _import_stubs():
    from app.generated import catalog_pb2, catalog_pb2_grpc, leads_pb2, leads_pb2_grpc

    return catalog_pb2, catalog_pb2_grpc, leads_pb2, leads_pb2_grpc


class CoreClient:
    def __init__(self, address: str | None = None):
        self._address = address or CORE_GRPC_ADDR
        self._channel = grpc.insecure_channel(self._address)
        catalog_pb2, catalog_pb2_grpc, leads_pb2, leads_pb2_grpc = _import_stubs()
        self._catalog_pb2 = catalog_pb2
        self._leads_pb2 = leads_pb2
        self._catalog = catalog_pb2_grpc.CatalogServiceStub(self._channel)
        self._leads = leads_pb2_grpc.LeadsServiceStub(self._channel)

    def get_seller(self, seller_id: int) -> dict:
        req = self._catalog_pb2.GetSellerRequest(id=seller_id)
        seller = self._catalog.GetSeller(req)
        return {
            "id": seller.id,
            "tg_user_id": seller.tg_user_id,
            "sensitivity": seller.sensitivity or "precise",
        }

    def list_products(self, seller_id: int, active_only: bool = True) -> list[dict]:
        req = self._catalog_pb2.ListProductsRequest(seller_id=seller_id, active_only=active_only)
        resp = self._catalog.ListProducts(req)
        return [
            {
                "id": p.id,
                "title": p.title,
                "keywords": list(p.keywords),
            }
            for p in resp.products
        ]

    def create_lead(self, payload: dict) -> int:
        req = self._leads_pb2.CreateLeadRequest(
            seller_id=payload["seller_id"],
            product_id=payload.get("product_id", 0),
            worker_id=payload.get("worker_id", 0),
            chat_id=payload["chat_id"],
            message_id=payload["message_id"],
            author_id=payload["author_id"],
            author_username=payload.get("author_username", ""),
            raw_text=payload["raw_text"],
            matched_keywords=payload.get("matched_keywords", []),
            product_score=payload.get("product_score", 0.0),
            intent_score=payload.get("intent_score", 0.0),
            score=payload.get("score", 0.0),
            level=payload["level"],
        )
        lead = self._leads.CreateLead(req)
        return lead.id

    def close(self) -> None:
        self._channel.close()


_core_client: CoreClient | None = None


def get_core_client() -> CoreClient:
    global _core_client
    if _core_client is None:
        _core_client = CoreClient()
    return _core_client
