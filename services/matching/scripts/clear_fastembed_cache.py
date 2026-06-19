#!/usr/bin/env python3
"""Remove fastembed ONNX download cache."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_publish_models():
    path = Path(__file__).resolve().parent / "publish_models.py"
    spec = importlib.util.spec_from_file_location("publish_models", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    publish_models = _load_publish_models()
    removed = publish_models.clear_fastembed_cache()
    if not removed:
        print("No fastembed cache directories found")
        return 0
    for path in removed:
        print(f"Removed {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
