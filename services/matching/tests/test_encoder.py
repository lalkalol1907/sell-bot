"""Unit tests for embedding encoder."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture
def mock_fastembed():
    fake = MagicMock()
    fake.embed.return_value = [np.array([0.1, 0.2, 0.3], dtype=np.float32)]
    with patch.dict("sys.modules", {"fastembed": MagicMock(TextEmbedding=MagicMock(return_value=fake))}):
        yield fake


def test_encode_text_mocked(mock_fastembed):
    from app.embeddings import encoder

    encoder.reset_encoder_cache()
    vectors = encoder.encode_texts(["куплю айфон"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 3


def test_resolve_embedding_model_dir_from_env(tmp_path, monkeypatch):
    model_dir = tmp_path / "onnx-model"
    model_dir.mkdir()
    monkeypatch.setenv("EMBEDDING_MODEL_DIR", str(model_dir))

    from app.embeddings import encoder

    encoder.reset_encoder_cache()
    assert encoder._resolve_embedding_model_dir() == model_dir


def test_encode_text_empty():
    from app.embeddings import encoder

    assert encoder.encode_texts([]) == []


def test_is_encoder_available_false_on_error():
    with patch.dict("sys.modules", {"fastembed": None}):
        from app.embeddings import encoder

        encoder.reset_encoder_cache()
        assert encoder.is_encoder_available() is False
