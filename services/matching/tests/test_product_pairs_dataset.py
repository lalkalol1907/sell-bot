"""Tests for variant-aware product pair matching."""

from pathlib import Path

import json

from app.config import fuzzy_min_score
from app.nlp.product_gate import match_product

ROOT = Path(__file__).resolve().parent.parent


def _product_from_row(row: dict) -> dict:
    product = {
        "id": 1,
        "title": row["product_title"],
        "keywords": row.get("keywords") or [row["product_title"]],
    }
    if row.get("storage_gb") is not None:
        product["storage_gb"] = row["storage_gb"]
    if row.get("color"):
        product["color"] = row["color"]
    return product


def _evaluate_pair(row: dict) -> tuple[bool, float]:
    expected = int(row["match"])
    product = _product_from_row(row)
    hit = match_product(row["message"], [product])
    threshold = fuzzy_min_score()
    predicted = 1 if hit is not None and hit.product_score >= threshold else 0
    score = hit.product_score if hit else 0.0
    return predicted == expected, score


def test_product_pairs_has_variant_rows():
    path = ROOT / "data" / "product_pairs_eval.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variant_neg = [r for r in rows if r.get("match") == 0 and ("256" in r["message"] or r.get("storage_gb"))]
    variant_pos = [r for r in rows if r.get("match") == 1 and ("256" in r["message"] or r.get("color"))]
    assert len(rows) >= 60
    assert len(variant_neg) >= 5
    assert len(variant_pos) >= 5


def test_variant_product_pairs_accuracy():
    path = ROOT / "data" / "product_pairs_eval.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    eval_rows = [r for r in rows if r.get("eval_scope") == "variant"]
    if not eval_rows:
        eval_rows = [
            r for r in rows
            if r.get("storage_gb") is not None
            or r.get("color") is not None
            or any(x in r["message"] for x in ("256", "512", "128", "1tb", "черн", "бел", "titanium", "син"))
        ]

    failures = []
    for row in eval_rows:
        ok, score = _evaluate_pair(row)
        if not ok:
            failures.append({
                "message": row["message"],
                "product_title": row["product_title"],
                "expected": row["match"],
                "score": round(score, 3),
            })

    assert not failures, f"variant pair failures: {failures}"
