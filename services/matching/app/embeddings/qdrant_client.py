"""Qdrant vector store client."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import EMBEDDING_DIM, QDRANT_COLLECTION, QDRANT_URL

_client = None


def get_qdrant_client():
    global _client
    if _client is not None:
        return _client

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    _client = QdrantClient(url=QDRANT_URL, timeout=10)
    collections = [c.name for c in _client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        _client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
    return _client


@dataclass
class SearchHit:
    product_id: int
    score: float


def upsert_product_vector(
    seller_id: int,
    product_id: int,
    vector: list[float],
    title: str,
) -> None:
    from qdrant_client.models import PointStruct

    client = get_qdrant_client()
    point_id = seller_id * 1_000_000 + product_id
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"seller_id": seller_id, "product_id": product_id, "title": title},
            )
        ],
    )


def delete_product_vector(seller_id: int, product_id: int) -> None:
    client = get_qdrant_client()
    point_id = seller_id * 1_000_000 + product_id
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=[point_id],
    )


def search_similar(seller_id: int, vector: list[float], limit: int = 3) -> list[SearchHit]:
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant_client()
    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vector,
        query_filter=Filter(
            must=[FieldCondition(key="seller_id", match=MatchValue(value=seller_id))]
        ),
        limit=limit,
    )
    hits: list[SearchHit] = []
    for r in results:
        pid = r.payload.get("product_id") if r.payload else None
        if pid is not None:
            hits.append(SearchHit(product_id=int(pid), score=float(r.score)))
    return hits


def reset_client() -> None:
    global _client
    _client = None
