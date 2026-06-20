"""Tests for intent training datasets."""

from pathlib import Path

import json

from app.training.datasets import generate_datasets

ROOT = Path(__file__).resolve().parent.parent


def test_generate_intent_datasets():
    generate_datasets()
    train = ROOT / "data" / "intent_train.jsonl"
    eval_path = ROOT / "data" / "intent_eval.jsonl"
    pairs = ROOT / "data" / "product_pairs_eval.jsonl"

    train_rows = [json.loads(line) for line in train.read_text(encoding="utf-8").splitlines() if line.strip()]
    eval_rows = [json.loads(line) for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pair_rows = [json.loads(line) for line in pairs.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(train_rows) >= 200
    assert len(eval_rows) >= 40
    assert len(pair_rows) >= 60


def test_intent_train_has_variant_buy_examples():
    path = ROOT / "data" / "intent_train.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variant_buy = [
        r for r in rows
        if r["label"] == "buy" and ("256" in r["text"] or "черн" in r["text"] or "white" in r["text"])
    ]
    assert len(variant_buy) >= 15
