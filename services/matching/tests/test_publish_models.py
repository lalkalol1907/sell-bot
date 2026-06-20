import pytest

from app.training.bundle import (
    EMBEDDING_SUBDIR,
    _onnx_model_path,
    resolve_fastembed_model_source,
)
from app.training.parity import clear_fastembed_cache


def test_resolve_prefers_valid_local_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "bundles" / "2026.06.18-1" / EMBEDDING_SUBDIR
    bundle.mkdir(parents=True)
    (bundle / "model_optimized.onnx").write_bytes(b"onnx")

    broken_cache = tmp_path / "fastembed_cache" / "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q"
    snapshots = broken_cache / "snapshots" / "deadbeef"
    snapshots.mkdir(parents=True)
    (snapshots / "model_optimized.onnx").symlink_to("/missing.onnx")

    monkeypatch.setattr("app.training.bundle.models_dir", lambda: tmp_path)
    monkeypatch.setattr(
        "app.training.bundle._fastembed_cache_roots",
        lambda: [tmp_path / "fastembed_cache"],
    )

    source = resolve_fastembed_model_source(models_root=tmp_path)
    assert source == bundle.resolve()


def test_onnx_model_path_ignores_broken_symlink(tmp_path):
    model_dir = tmp_path / "embedding"
    model_dir.mkdir()
    (model_dir / "model_optimized.onnx").symlink_to("/missing.onnx")

    assert _onnx_model_path(model_dir) is None

    (model_dir / "model.onnx").write_bytes(b"onnx")
    assert _onnx_model_path(model_dir).name == "model.onnx"


def test_clear_fastembed_cache(tmp_path, monkeypatch):
    cache_root = tmp_path / "fastembed_cache"
    cache_root.mkdir()
    (cache_root / "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q").mkdir()

    monkeypatch.setattr("app.training.parity.fastembed_cache_roots", lambda: [cache_root])

    removed = clear_fastembed_cache()
    assert removed == [cache_root]
    assert not cache_root.exists()
