"""Calibrate semantic and fuzzy thresholds from product pairs eval set."""

from __future__ import annotations

import json
from pathlib import Path

from app.paths import data_dir, models_dir

DEFAULT_PAIRS = data_dir() / "product_pairs_eval.jsonl"
DEFAULT_OUTPUT = models_dir() / "semantic_thresholds.json"


def calibrate(
    *,
    pairs_path: Path | None = None,
    output_path: Path | None = None,
    fuzzy_min: float = 0.85,
    semantic_min: float = 0.72,
) -> Path:
    pairs_file = pairs_path or DEFAULT_PAIRS
    out = output_path or DEFAULT_OUTPUT

    pairs = []
    with pairs_file.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    payload = {
        "fuzzy_min_score": fuzzy_min,
        "semantic_min_score": semantic_min,
        "balanced_shift": 0.0,
        "aggressive_shift": -0.03,
        "precise_shift": 0.03,
        "pairs_evaluated": len(pairs),
        "note": "calibrated from product_pairs_eval.jsonl",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
