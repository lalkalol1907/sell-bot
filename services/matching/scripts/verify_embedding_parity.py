#!/usr/bin/env python3
"""Compare sentence-transformers vs fastembed ONNX embedding parity."""

from __future__ import annotations

import argparse
import sys

import numpy as np

SAMPLE_TEXTS = [
    "куплю айфон 16",
    "ищу iphone 16 pro",
    "где достать шестнадцатый про?",
    "нужен samsung s24",
    "продаю macbook pro",
    "у меня айфон тормозит",
    "где взять галакси эс 24",
    "ищу шестнадцатую прошку",
    "есть у кого 16 про на 256?",
    "подскажите шестнадцатый про 256",
    "куплю iphone 16 pro 256 черный",
    "нужен galaxy s24 256 синий",
    "достать пятнадцатую модель",
    "где купить эс двадцать четыре",
    "ищу макбук на m3",
    "нужны беспроводные эйрподсы про",
    "где найти плейстейшн пять",
    "ищу планшет эйр от эпл",
    "есть кто продаёт шестнадцатый? нет, ищу купить",
    "привет всем",
]

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


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


def check_parity(model_dir: str, *, max_drift: float = 0.02) -> dict:
    st_vectors = _encode_sentence_transformers(SAMPLE_TEXTS)
    onnx_vectors = _encode_fastembed(SAMPLE_TEXTS, model_dir)

    drifts = [_cosine(a, b) for a, b in zip(st_vectors, onnx_vectors, strict=True)]
    worst = min(drifts)
    return {
        "samples": len(drifts),
        "min_cosine": worst,
        "max_drift": 1.0 - worst,
        "passed": (1.0 - worst) <= max_drift,
        "max_allowed_drift": max_drift,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True, help="Path to ONNX embedding directory")
    parser.add_argument("--max-drift", type=float, default=0.02)
    args = parser.parse_args()

    report = check_parity(args.model_dir, max_drift=args.max_drift)
    print(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
