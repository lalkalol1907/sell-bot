"""Tests for runtime model hot-reload."""

from pathlib import Path
from unittest.mock import patch

import pytest


def _bundle(tmp_path, version: str) -> tuple[Path, Path, Path]:
    import joblib
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    bundle = tmp_path / version
    embedding = bundle / "embedding" / "paraphrase-multilingual-MiniLM-L12-v2"
    embedding.mkdir(parents=True)
    (embedding / "model.onnx").write_bytes(b"onnx")
    intent = bundle / "intent.joblib"
    vec = CountVectorizer()
    x = vec.fit_transform(["куплю iphone", "продаю iphone"])
    clf = LogisticRegression()
    clf.fit(x, ["buy", "sell"])
    joblib.dump({"classifier": clf, "vectorizer": vec, "feature_type": "tfidf"}, intent)
    (bundle / "semantic_thresholds.json").write_text(
        '{"fuzzy_min_score":0.85,"semantic_min_score":0.72}', encoding="utf-8"
    )
    (bundle / "manifest.json").write_text(
        '{"version": "%s", "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"}'
        % version,
        encoding="utf-8",
    )
    return bundle, embedding, intent


def test_apply_bundle_updates_env_and_version(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))
    bundle, embedding, intent = _bundle(tmp_path, "2026.06.19-1")

    from app import models_runtime
    from app.models_sync import SyncResult

    result = SyncResult(
        version="2026.06.19-1",
        local_dir=bundle,
        intent_model_path=intent,
        embedding_model_dir=embedding,
    )
    with patch.object(models_runtime, "warmup_models"):
        models_runtime.apply_bundle(result)

    import os

    assert os.environ["INTENT_MODEL_PATH"] == str(intent)
    assert os.environ["EMBEDDING_MODEL_DIR"] == str(embedding)
    assert models_runtime.current_version() == "2026.06.19-1"


def test_apply_bundle_resets_caches(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))
    bundle, embedding, intent = _bundle(tmp_path, "v1")

    from app import models_runtime
    from app.embeddings import indexer
    from app.embeddings.encoder import reset_encoder_cache
    from app.models_sync import SyncResult
    from app.nlp.intent_classifier import reset_model_cache

    indexer._local_indexed[(1, "hash", "old")] = True
    result = SyncResult(
        version="v1",
        local_dir=bundle,
        intent_model_path=intent,
        embedding_model_dir=embedding,
    )
    with patch.object(models_runtime, "warmup_models"):
        models_runtime.apply_bundle(result)

    import os

    assert indexer._model_version == "v1"
    assert (1, "hash", "old") not in indexer._local_indexed
    reset_encoder_cache()
    reset_model_cache()
    assert os.environ["INTENT_MODEL_PATH"] == str(intent)


def test_apply_bundle_rejects_incompatible_embedding(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))
    bundle, embedding, intent = _bundle(tmp_path, "bad")
    (bundle / "manifest.json").write_text(
        '{"version": "bad", "embedding_model": "other/model"}',
        encoding="utf-8",
    )

    from app import models_runtime
    from app.models_sync import SyncResult

    result = SyncResult(
        version="bad",
        local_dir=bundle,
        intent_model_path=intent,
        embedding_model_dir=embedding,
    )
    with pytest.raises(RuntimeError, match="incompatible embedding model"):
        models_runtime.apply_bundle(result)


def test_reload_if_changed_noop_when_same_version(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")

    from app import models_runtime

    with patch.object(models_runtime, "current_version", return_value="2026.06.19-1"):
        with patch("app.models_runtime.peek_remote_version", return_value="2026.06.19-1"):
            assert models_runtime.reload_if_changed() is False


def test_reload_if_changed_downloads_new_version(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("MODELS_LOCAL_DIR", str(tmp_path))

    bundle, embedding, intent = _bundle(tmp_path, "2026.06.20-1")
    from app import models_runtime
    from app.models_sync import SyncResult

    fake = SyncResult(
        version="2026.06.20-1",
        local_dir=bundle,
        intent_model_path=intent,
        embedding_model_dir=embedding,
    )

    with patch.object(models_runtime, "current_version", return_value="2026.06.19-1"):
        with patch("app.models_runtime.peek_remote_version", return_value="2026.06.20-1"):
            with patch("app.models_runtime.sync_models_from_s3", return_value=fake):
                with patch.object(models_runtime, "warmup_models"):
                    assert models_runtime.reload_if_changed() is True
    assert models_runtime.current_version() == "2026.06.20-1"


def test_reload_if_changed_skips_when_pinned(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("MODELS_S3_VERSION", "pinned-v1")

    from app import models_runtime

    with patch("app.models_runtime.peek_remote_version", return_value="new-v2") as peek:
        assert models_runtime.reload_if_changed() is False
        peek.assert_not_called()


def test_warmup_models_loads_intent_and_encoder(tmp_path, monkeypatch):
    import joblib
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression
    from unittest.mock import MagicMock

    import numpy as np

    fake = MagicMock()
    fake.embed.return_value = [np.array([0.1, 0.2, 0.3], dtype=np.float32)]

    monkeypatch.setenv("EMBEDDING_MODEL_DIR", str(tmp_path / "onnx"))
    (tmp_path / "onnx").mkdir()
    intent = tmp_path / "intent.joblib"
    vec = CountVectorizer()
    x = vec.fit_transform(["куплю iphone", "продаю iphone"])
    clf = LogisticRegression()
    clf.fit(x, ["buy", "sell"])
    joblib.dump({"classifier": clf, "vectorizer": vec, "feature_type": "tfidf"}, intent)
    monkeypatch.setenv("INTENT_MODEL_PATH", str(intent))

    from app.embeddings import encoder
    from app import models_runtime
    from app.nlp import intent_classifier

    encoder.reset_encoder_cache()
    intent_classifier.reset_model_cache()

    with patch.dict("sys.modules", {"fastembed": MagicMock(TextEmbedding=MagicMock(return_value=fake))}):
        models_runtime.warmup_models()

    fake.embed.assert_called()
    assert intent_classifier._classifier is not None


def test_intent_classifier_uses_updated_path(tmp_path, monkeypatch, reload_modules):
    import joblib
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    from app.nlp.normalize import normalize_text

    model_a = tmp_path / "intent_a.joblib"
    model_b = tmp_path / "intent_b.joblib"
    texts = [normalize_text("куплю iphone"), normalize_text("продаю iphone")]
    for path, labels in ((model_a, ["buy", "sell"]), (model_b, ["sell", "buy"])):
        vec = CountVectorizer()
        x = vec.fit_transform(texts)
        clf = LogisticRegression()
        clf.fit(x, labels)
        joblib.dump({"classifier": clf, "vectorizer": vec, "feature_type": "tfidf"}, path)

    monkeypatch.setenv("INTENT_MODEL_PATH", str(model_a))
    reload_modules()

    from app.nlp.intent_classifier import classify_intent, reset_model_cache

    assert classify_intent(normalize_text("куплю iphone")).label == "buy"

    monkeypatch.setenv("INTENT_MODEL_PATH", str(model_b))
    reset_model_cache()
    assert classify_intent(normalize_text("куплю iphone")).label == "sell"
