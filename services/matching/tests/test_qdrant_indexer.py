"""Integration tests for Qdrant indexer (optional, requires Qdrant)."""

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def qdrant_available():
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    try:
        import httpx

        resp = httpx.get(f"{url}/collections", timeout=2.0)
        if resp.status_code != 200:
            pytest.skip("Qdrant not available")
    except Exception:
        pytest.skip("Qdrant not available")
    return url


def test_qdrant_upsert_search_delete(monkeypatch, reload_modules, qdrant_available):
    monkeypatch.setenv("QDRANT_URL", qdrant_available)
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    reload_modules()

    from app.embeddings.qdrant_client import delete_product_vector, reset_client, search_similar, upsert_product_vector

    reset_client()
    vector = [0.1] * 384
    upsert_product_vector(99, 1, vector, "Test Product")
    hits = search_similar(99, vector, limit=1)
    assert hits
    assert hits[0].product_id == 1
    delete_product_vector(99, 1)
