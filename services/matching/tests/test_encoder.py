"""Unit tests for embedding encoder."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_sentence_transformers():
    fake = MagicMock()
    fake.encode.return_value = [[0.1, 0.2, 0.3]]
    with patch.dict("sys.modules", {"sentence_transformers": MagicMock(SentenceTransformer=MagicMock(return_value=fake))}):
        yield fake


def test_encode_text_mocked(mock_sentence_transformers):
    import numpy as np
    from app.embeddings import encoder

    mock_sentence_transformers.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    encoder._load_encoder.cache_clear()
    encoder._encoder = None
    vectors = encoder.encode_texts(["куплю айфон"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 3


def test_is_encoder_available_false_on_error():
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        from app.embeddings import encoder

        encoder._load_encoder.cache_clear()
        encoder._encoder = None
        assert encoder.is_encoder_available() is False
