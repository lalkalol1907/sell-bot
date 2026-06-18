"""Integration parity check between sentence-transformers and fastembed ONNX."""

import pytest

pytestmark = pytest.mark.integration


def test_embedding_parity_with_cached_onnx(tmp_path):
    pytest.importorskip("sentence_transformers")

    from scripts.publish_models import _resolve_fastembed_model_source
    from scripts.verify_embedding_parity import MODEL_NAME, check_parity

    model_dir = tmp_path / "embedding"
    try:
        source_dir = _resolve_fastembed_model_source(MODEL_NAME)
    except RuntimeError:
        pytest.skip("ONNX model not available from fastembed")

    import shutil

    shutil.copytree(source_dir, model_dir, dirs_exist_ok=True)
    report = check_parity(str(model_dir), max_drift=0.05)
    assert report["passed"]
