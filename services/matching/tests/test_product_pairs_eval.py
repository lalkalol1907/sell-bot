"""Tests for product_pairs_eval dataset consistency."""

from pathlib import Path

import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def test_product_pairs_has_variant_rows():
    path = ROOT / "data" / "product_pairs_eval.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variant_neg = [r for r in rows if r.get("match") == 0 and ("256" in r["message"] or r.get("storage_gb"))]
    variant_pos = [r for r in rows if r.get("match") == 1 and ("256" in r["message"] or r.get("color"))]
    assert len(rows) >= 60
    assert len(variant_neg) >= 5
    assert len(variant_pos) >= 5


def test_eval_product_pairs_script():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval_product_pairs.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_intent_train_has_variant_buy_examples():
    path = ROOT / "data" / "intent_train.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variant_buy = [r for r in rows if r["label"] == "buy" and ("256" in r["text"] or "черн" in r["text"] or "white" in r["text"])]
    assert len(variant_buy) >= 15
