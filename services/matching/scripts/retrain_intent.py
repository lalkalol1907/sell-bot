#!/usr/bin/env python3
"""Retrain intent model with version bump."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"


def next_version() -> str:
    versions = []
    for path in MODELS.glob("intent_v*.joblib"):
        m = re.search(r"intent_v(\d+)", path.stem)
        if m:
            versions.append(int(m.group(1)))
    n = max(versions) + 1 if versions else 1
    return f"intent_v{n}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=None, help="Output model name stem, e.g. intent_v2")
    parser.add_argument("--no-embeddings", action="store_true")
    args = parser.parse_args()

    version = args.version or next_version()
    output = MODELS / f"{version}.joblib"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "train_intent.py"),
        "--output",
        str(output),
    ]
    if args.no_embeddings:
        cmd.append("--no-embeddings")

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        print(f"Deployed artifact: {output}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
