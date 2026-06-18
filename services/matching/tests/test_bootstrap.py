"""Tests for model bootstrap."""

from pathlib import Path
from unittest.mock import patch

import pytest


def test_bootstrap_local_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_SKIP_S3", "true")
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))
    monkeypatch.setenv("NLP_V2_INTENT_ML", "false")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "false")

    intent = tmp_path / "intent_v1.joblib"
    intent.write_bytes(b"model")
    embedding = tmp_path / "embedding" / "paraphrase-multilingual-MiniLM-L12-v2"
    embedding.mkdir(parents=True)
    (embedding / "model.onnx").write_bytes(b"onnx")

    from app.bootstrap import bootstrap_models

    bootstrap_models()

    import os

    assert os.environ["INTENT_MODEL_PATH"] == str(intent)
    assert os.environ["EMBEDDING_MODEL_DIR"] == str(embedding)


def test_bootstrap_fails_when_s3_required_but_missing(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("MODELS_S3_PREFIX", "dev")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    monkeypatch.delenv("MODELS_SKIP_S3", raising=False)

    from app import bootstrap

    with pytest.raises(SystemExit):
        bootstrap.bootstrap_models()


def test_bootstrap_with_mocked_s3_sync(monkeypatch, tmp_path):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    monkeypatch.setenv("NLP_V2_INTENT_ML", "true")

    embedding = tmp_path / "v1" / "embedding" / "paraphrase-multilingual-MiniLM-L12-v2"
    embedding.mkdir(parents=True)
    (embedding / "model.onnx").write_bytes(b"onnx")
    intent = tmp_path / "v1" / "intent_v1.joblib"
    intent.write_bytes(b"model")

    from app import bootstrap
    from app import models_sync

    fake = models_sync.SyncResult(
        version="v1",
        local_dir=tmp_path / "v1",
        intent_model_path=intent,
        embedding_model_dir=embedding,
    )
    with patch.object(bootstrap, "sync_models_from_s3", return_value=fake):
        bootstrap.bootstrap_models()

    import os

    assert os.environ["INTENT_MODEL_PATH"] == str(intent)
    assert os.environ["EMBEDDING_MODEL_DIR"] == str(embedding)
