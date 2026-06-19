import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_publish_models():
    path = ROOT / "scripts" / "publish_models.py"
    spec = importlib.util.spec_from_file_location("publish_models", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_prefers_valid_local_bundle(tmp_path, monkeypatch):
    publish_models = _load_publish_models()

    bundle = tmp_path / "bundles" / "2026.06.18-1" / publish_models.EMBEDDING_SUBDIR
    bundle.mkdir(parents=True)
    (bundle / "model_optimized.onnx").write_bytes(b"onnx")

    broken_cache = tmp_path / "fastembed_cache" / "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q"
    snapshots = broken_cache / "snapshots" / "deadbeef"
    snapshots.mkdir(parents=True)
    (snapshots / "model_optimized.onnx").symlink_to("/missing.onnx")

    monkeypatch.setattr(publish_models, "MODELS", tmp_path)
    monkeypatch.setattr(
        publish_models,
        "_fastembed_cache_roots",
        lambda: [tmp_path / "fastembed_cache"],
    )

    source = publish_models._resolve_fastembed_model_source(publish_models.MODEL_NAME)
    assert source == bundle.resolve()


def test_onnx_model_path_ignores_broken_symlink(tmp_path):
    publish_models = _load_publish_models()

    model_dir = tmp_path / "embedding"
    model_dir.mkdir()
    (model_dir / "model_optimized.onnx").symlink_to("/missing.onnx")

    assert publish_models._onnx_model_path(model_dir) is None

    (model_dir / "model.onnx").write_bytes(b"onnx")
    assert publish_models._onnx_model_path(model_dir).name == "model.onnx"


def test_clear_fastembed_cache(tmp_path, monkeypatch):
    publish_models = _load_publish_models()

    cache_root = tmp_path / "fastembed_cache"
    cache_root.mkdir()
    (cache_root / "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q").mkdir()

    monkeypatch.setattr(publish_models, "_fastembed_cache_roots", lambda: [cache_root])

    removed = publish_models.clear_fastembed_cache()
    assert removed == [cache_root]
    assert not cache_root.exists()
