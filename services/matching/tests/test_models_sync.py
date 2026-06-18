"""Tests for S3 model sync."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_should_sync_models_requires_bucket(monkeypatch):
    monkeypatch.delenv("MODELS_SKIP_S3", raising=False)
    monkeypatch.delenv("MODELS_S3_BUCKET", raising=False)
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

    from app import models_sync

    assert models_sync.should_sync_models() is False


def test_should_sync_models_when_configured(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

    from app import models_sync

    assert models_sync.should_sync_models() is True


def test_should_skip_when_flags_disabled(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "false")
    monkeypatch.setenv("NLP_V2_INTENT_ML", "false")

    from app import models_sync

    assert models_sync.should_sync_models() is False


def test_download_bundle_verifies_checksum(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")

    manifest = {
        "version": "v1",
        "files": [
            {"path": "intent_v1.joblib", "sha256": "abc", "size": 3},
        ],
    }
    client = MagicMock()
    client.get_object.side_effect = [
        {"Body": MagicMock(read=lambda: __import__("json").dumps(manifest).encode())},
    ]

    def fake_download(bucket, key, dest):
        Path(dest).write_bytes(b"bad")

    client.download_file.side_effect = fake_download

    from app import models_sync

    with patch.object(models_sync, "_s3_client", return_value=client):
        with pytest.raises(RuntimeError, match="checksum mismatch"):
            models_sync._download_bundle(client, "sellbot", "", "v1", tmp_path)


def test_download_bundle_success(tmp_path):
    bundle_file = tmp_path / "intent_v1.joblib"
    bundle_file.write_bytes(b"abc")
    import hashlib

    digest = hashlib.sha256(b"abc").hexdigest()
    manifest = {
        "version": "v1",
        "files": [{"path": "intent_v1.joblib", "sha256": digest, "size": 3}],
    }
    client = MagicMock()
    client.get_object.return_value = {
        "Body": MagicMock(read=lambda: __import__("json").dumps(manifest).encode())
    }

    def fake_download(bucket, key, dest):
        Path(dest).write_bytes(b"abc")

    client.download_file.side_effect = fake_download

    from app import models_sync

    result = models_sync._download_bundle(client, "sellbot", "dev", "v1", tmp_path)
    assert result.version == "v1"
    assert result.intent_model_path == tmp_path / "v1" / "intent_v1.joblib"


def test_sync_models_from_s3_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

    from app import models_sync

    fake_result = models_sync.SyncResult(
        version="v1",
        local_dir=tmp_path / "v1",
        intent_model_path=tmp_path / "v1" / "intent_v1.joblib",
        embedding_model_dir=tmp_path / "v1" / models_sync.EMBEDDING_SUBDIR,
    )
    with patch.object(models_sync, "_s3_client", return_value=MagicMock()):
        with patch.object(models_sync, "_resolve_version", return_value="v1"):
            with patch.object(models_sync, "_download_bundle", return_value=fake_result):
                result = models_sync.sync_models_from_s3()
    assert result is not None
    assert result.version == "v1"
