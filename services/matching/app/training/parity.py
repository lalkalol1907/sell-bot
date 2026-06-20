"""Compare sentence-transformers vs fastembed ONNX embedding parity."""

from __future__ import annotations

import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.paths import data_dir

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_HINT = "paraphrase-multilingual-minilm-l12-v2"
ONNX_FILENAMES = ("model.onnx", "model_optimized.onnx")
PARITY_SAMPLES_PATH = data_dir() / "embedding_parity_samples.txt"


@lru_cache(maxsize=1)
def load_sample_texts(path: str | None = None) -> tuple[str, ...]:
    sample_path = Path(path) if path else PARITY_SAMPLES_PATH
    lines = sample_path.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip())


SAMPLE_TEXTS = load_sample_texts()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _encode_sentence_transformers(texts: list[str]) -> list[np.ndarray]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    vectors = model.encode(texts, normalize_embeddings=True)
    return [np.asarray(v, dtype=np.float32) for v in vectors]


def _encode_fastembed(texts: list[str], model_dir: str) -> list[np.ndarray]:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=MODEL_NAME, specific_model_path=model_dir)
    vectors = list(model.embed(texts, batch_size=32))
    normalized = []
    for vector in vectors:
        arr = np.asarray(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        normalized.append(arr)
    return normalized


def check_parity(model_dir: str | Path, *, max_drift: float = 0.02) -> dict:
    model_dir = str(model_dir)
    texts = list(load_sample_texts())
    st_vectors = _encode_sentence_transformers(texts)
    onnx_vectors = _encode_fastembed(texts, model_dir)

    drifts = [_cosine(a, b) for a, b in zip(st_vectors, onnx_vectors, strict=True)]
    worst = min(drifts)
    return {
        "samples": len(drifts),
        "min_cosine": worst,
        "max_drift": 1.0 - worst,
        "passed": (1.0 - worst) <= max_drift,
        "max_allowed_drift": max_drift,
    }


def fastembed_cache_roots() -> list[Path]:
    roots = [
        Path(os.getenv("FASTEMBED_CACHE_PATH", Path(tempfile.gettempdir()) / "fastembed_cache")),
        Path.home() / ".cache" / "fastembed",
    ]
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        resolved = root.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def clear_fastembed_cache() -> list[Path]:
    removed: list[Path] = []
    for cache_root in fastembed_cache_roots():
        if not cache_root.is_dir():
            continue
        shutil.rmtree(cache_root, ignore_errors=True)
        removed.append(cache_root)
    return removed
