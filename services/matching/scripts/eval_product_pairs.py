#!/usr/bin/env python3
"""Validate variant-aware product pairs from product_pairs_eval.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import FUZZY_MIN_SCORE
from app.nlp.product_gate import match_product

DEFAULT_PAIRS = ROOT / "data" / "product_pairs_eval.jsonl"


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


def evaluate_pair(row: dict) -> tuple[bool, float]:
    expected = int(row["match"])
    product = _product_from_row(row)
    hit = match_product(row["message"], [product])
    predicted = 1 if hit is not None and hit.product_score >= FUZZY_MIN_SCORE else 0
    score = hit.product_score if hit else 0.0
    return predicted == expected, score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    args = parser.parse_args()

    rows = []
    with args.pairs.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

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
        ok, score = evaluate_pair(row)
        if not ok:
            failures.append({
                "message": row["message"],
                "product_title": row["product_title"],
                "expected": row["match"],
                "score": round(score, 3),
            })

    report = {
        "pairs_total": len(rows),
        "variant_pairs_evaluated": len(eval_rows),
        "accuracy": (len(eval_rows) - len(failures)) / len(eval_rows) if eval_rows else 1.0,
        "failures_count": len(failures),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps(failures, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
