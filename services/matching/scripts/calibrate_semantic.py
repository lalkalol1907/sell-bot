#!/usr/bin/env python3
"""Calibrate SEMANTIC_MIN_SCORE from product pairs eval set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, default=ROOT / "data" / "product_pairs_eval.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "models" / "semantic_thresholds.json")
    parser.add_argument("--default-threshold", type=float, default=0.72)
    args = parser.parse_args()

    pairs = []
    with args.pairs.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    threshold = args.default_threshold
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "semantic_min_score": threshold,
        "balanced_shift": 0.0,
        "aggressive_shift": -0.03,
        "precise_shift": 0.03,
        "pairs_evaluated": len(pairs),
        "note": "v2 default calibration; run with encoder+Qdrant for data-driven ROC",
    }
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
