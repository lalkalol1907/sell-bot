"""Integration parity check between sentence-transformers and fastembed ONNX."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_embedding_parity_with_cached_onnx(tmp_path):
    pytest.importorskip("sentence_transformers")
    from fastembed import TextEmbedding

    from scripts.verify_embedding_parity import MODEL_NAME, check_parity

    model_dir = tmp_path / "embedding"
    model_dir.mkdir()
    TextEmbedding(model_name=MODEL_NAME)
    cache_root = Path.home() / ".cache" / "fastembed"
    source_dir = None
    for path in cache_root.rglob("model.onnx"):
        if "paraphrase-multilingual-MiniLM-L12-v2" in str(path):
            source_dir = path.parent
            break
    if source_dir is None:
        pytest.skip("ONNX model not present in fastembed cache")

    import shutil

    shutil.copytree(source_dir, model_dir, dirs_exist_ok=True)
    report = check_parity(str(model_dir), max_drift=0.05)
    assert report["passed"]
