"""Resolve matching service root for data/ and models/ paths."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_CASES_MARKER = Path("data") / "recognition_cases.yaml"


@lru_cache(maxsize=1)
def project_root() -> Path:
    env = os.getenv("MATCHING_ROOT", "").strip()
    if env:
        root = Path(env).resolve()
        if (root / _CASES_MARKER).is_file():
            return root

    cwd = Path.cwd().resolve()
    if (cwd / _CASES_MARKER).is_file():
        return cwd

    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here.parent.parent):
        if (candidate / _CASES_MARKER).is_file():
            return candidate

    return here.parent


def data_dir() -> Path:
    return project_root() / "data"


def models_dir() -> Path:
    return project_root() / "models"
