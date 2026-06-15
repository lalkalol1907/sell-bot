"""Unit tests for catalog indexer."""

from unittest.mock import MagicMock, patch


def test_catalog_hash_stable(reload_modules):
    from app.embeddings.indexer import _catalog_hash

    products = [{"id": 1, "title": "A", "keywords": ["x"]}]
    assert _catalog_hash(products) == _catalog_hash(products)


def test_search_products_success(monkeypatch, reload_modules):
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    from app.embeddings import indexer

    with patch.object(indexer, "ensure_catalog_indexed"):
        with patch.object(indexer, "encode_text", return_value=[0.1] * 384):
            with patch.object(indexer, "search_similar", return_value=[MagicMock(product_id=7, score=0.8)]):
                hits = indexer.search_products(1, "куплю", [{"id": 7, "title": "Phone"}], limit=1)
                assert hits
                assert hits[0].product_id == 7


def test_ensure_catalog_indexed_without_redis(monkeypatch, reload_modules):
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    reload_modules()
    import importlib

    from app.embeddings import indexer

    importlib.reload(indexer)

    products = [{"id": 1, "title": "Phone", "keywords": ["phone"]}]
    indexer._local_indexed.clear()
    with patch.object(indexer, "_get_redis", side_effect=ConnectionError("no redis")):
        with patch("app.embeddings.encoder.encode_texts", return_value=[[0.2] * 384]):
            with patch.object(indexer, "upsert_product_vector") as upsert:
                indexer.ensure_catalog_indexed(1, products)
                upsert.assert_called_once()
