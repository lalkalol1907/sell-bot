"""Catalog indexing and semantic search."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass

import redis

from app.config import REDIS_URL
from app.embeddings.encoder import encode_text
from app.embeddings.qdrant_client import upsert_product_vector
from app.handlers import metrics
from app.nlp.normalize import normalize_text

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None
_local_indexed: dict[tuple[int, str, str], bool] = {}
_model_version: str = "unknown"


def reset_index_cache(model_version: str) -> None:
    global _model_version
    _model_version = model_version
    _local_indexed.clear()


def _active_model_version() -> str:
    try:
        from app.models_runtime import current_version

        version = current_version()
        if version:
            return version
    except Exception:
        pass
    return _model_version


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
                }
                for p in products
            ],
            key=lambda x: x["id"],
        ),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def ensure_catalog_indexed(seller_id: int, products: list[dict]) -> None:
    if not products:
        return

    model_version = _active_model_version()
    key = f"catalog:hash:{seller_id}:{model_version}"
    current = _catalog_hash(products)
    cache_key = (seller_id, current, model_version)
    if _local_indexed.get(cache_key):
        return

    redis_client = None
    try:
        redis_client = _get_redis()
        if redis_client.get(key) == current:
            _local_indexed[cache_key] = True
            return
    except Exception as exc:
        logger.warning("catalog index redis check failed seller=%s: %s", seller_id, exc)
        metrics.SEMANTIC_ERRORS.labels(stage="index_redis").inc()
        redis_client = None

    from app.embeddings.encoder import encode_texts

    texts = []
    for p in products:
        kw = " ".join(p.get("keywords") or [])
        raw = f"{p.get('title', '')} {kw}".strip()
        texts.append(normalize_text(raw))

    try:
        from app.embeddings.qdrant_client import upsert_product_vector

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
    except Exception as exc:
        logger.warning("catalog index failed seller=%s: %s", seller_id, exc)
        metrics.SEMANTIC_ERRORS.labels(stage="index").inc()


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
    except Exception as exc:
        logger.warning("ensure_catalog_indexed failed seller=%s: %s", seller_id, exc)
        metrics.SEMANTIC_ERRORS.labels(stage="search_index").inc()

    try:
        from app.embeddings.qdrant_client import search_similar

        vector = encode_text(normalized_text)
        hits = search_similar(seller_id, vector, limit=limit)
        if not hits:
            return []
        return [ProductSearchHit(product_id=hit.product_id, score=float(hit.score)) for hit in hits]
    except Exception as exc:
        logger.warning("semantic search failed seller=%s: %s", seller_id, exc)
        metrics.SEMANTIC_ERRORS.labels(stage="search").inc()
        return []
