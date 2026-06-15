"""Catalog indexing and semantic search."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import redis

from app.config import NLP_V2_SEMANTIC, REDIS_URL
from app.embeddings.encoder import encode_text
from app.embeddings.qdrant_client import SearchHit, search_similar, upsert_product_vector
from app.nlp.normalize import normalize_text

_redis: redis.Redis | None = None
_local_indexed: dict[tuple[int, str], bool] = {}


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
    return _redis


def _catalog_hash(products: list[dict]) -> str:
    payload = json.dumps(
        sorted(
            [
                {
                    "id": p["id"],
                    "title": p.get("title", ""),
                    "keywords": sorted(p.get("keywords") or []),
                    "storage_gb": p.get("storage_gb"),
                    "color": p.get("color"),
                }
                for p in products
            ],
            key=lambda x: x["id"],
        ),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def ensure_catalog_indexed(seller_id: int, products: list[dict]) -> None:
    if not NLP_V2_SEMANTIC or not products:
        return

    key = f"catalog:hash:{seller_id}"
    current = _catalog_hash(products)
    cache_key = (seller_id, current)
    if _local_indexed.get(cache_key):
        return

    redis_client = None
    try:
        redis_client = _get_redis()
        if redis_client.get(key) == current:
            _local_indexed[cache_key] = True
            return
    except Exception:
        redis_client = None

    from app.embeddings.encoder import encode_texts

    texts = []
    for p in products:
        kw = " ".join(p.get("keywords") or [])
        storage = p.get("storage_gb")
        color = p.get("color")
        extra = []
        if storage is not None:
            extra.append(f"{storage}gb")
        if color:
            extra.append(str(color))
        raw = f"{p.get('title', '')} {kw} {' '.join(extra)}".strip()
        texts.append(normalize_text(raw))

    try:
        vectors = encode_texts(texts)
        for product, vector in zip(products, vectors):
            upsert_product_vector(
                seller_id,
                product["id"],
                vector,
                product.get("title", ""),
            )
        if redis_client is not None:
            redis_client.set(key, current, ex=86400)
        _local_indexed[cache_key] = True
    except Exception:
        pass


@dataclass
class ProductSearchHit:
    product_id: int
    score: float


def search_products(
    seller_id: int,
    normalized_text: str,
    products: list[dict],
    limit: int = 1,
) -> list[ProductSearchHit]:
    try:
        ensure_catalog_indexed(seller_id, products)
    except Exception:
        pass
    try:
        vector = encode_text(normalized_text)
        hits = search_similar(seller_id, vector, limit=limit)
        if not hits:
            return []
        return [ProductSearchHit(product_id=hit.product_id, score=float(hit.score)) for hit in hits]
    except Exception:
        return []
