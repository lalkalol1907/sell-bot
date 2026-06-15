"""Unit tests for Qdrant client wrappers."""

from unittest.mock import MagicMock, patch


def test_get_qdrant_client_creates_collection(monkeypatch, reload_modules):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []

    with patch("qdrant_client.QdrantClient", return_value=mock_client):
        from app.embeddings import qdrant_client

        qdrant_client.reset_client()
        client = qdrant_client.get_qdrant_client()
        assert client is mock_client
        mock_client.create_collection.assert_called_once()


def test_search_similar_maps_payload(monkeypatch, reload_modules):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    hit = MagicMock()
    hit.score = 0.9
    hit.payload = {"product_id": 42}
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = [MagicMock(name="products")]
    mock_client.search.return_value = [hit]

    with patch("qdrant_client.QdrantClient", return_value=mock_client):
        from app.embeddings import qdrant_client

        qdrant_client.reset_client()
        results = qdrant_client.search_similar(1, [0.1] * 384)
        assert results[0].product_id == 42
        assert results[0].score == 0.9


def test_upsert_and_delete_vector(monkeypatch, reload_modules):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = [MagicMock(name="products")]

    with patch("qdrant_client.QdrantClient", return_value=mock_client):
        from app.embeddings import qdrant_client

        qdrant_client.reset_client()
        qdrant_client.upsert_product_vector(1, 2, [0.1] * 384, "Phone")
        qdrant_client.delete_product_vector(1, 2)
        assert mock_client.upsert.called
        assert mock_client.delete.called
