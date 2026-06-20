"""Bootstrap runtime model paths before serving traffic."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from app.config import INTENT_MODEL_NAME, THRESHOLDS_NAME, load_thresholds
from app.models_runtime import apply_bundle
from app.models_sync import (
    EMBEDDING_SUBDIR,
    SyncResult,
    find_local_bundle,
    should_sync_models,
    sync_models_from_s3,
)
from app.paths import models_dir

logger = logging.getLogger(__name__)


def _local_models_dir() -> Path:
    return Path(os.getenv("MODELS_LOCAL_DIR", str(models_dir())))


def _apply_local_defaults() -> None:
    root = _local_models_dir()
    local = find_local_bundle(root)
    if local is not None:
        apply_bundle(local)
        return

    intent = root / INTENT_MODEL_NAME
    embedding = root / EMBEDDING_SUBDIR
    thresholds = root / THRESHOLDS_NAME

    if intent.is_file():
        os.environ.setdefault("INTENT_MODEL_PATH", str(intent))
    if embedding.is_dir():
        os.environ.setdefault("EMBEDDING_MODEL_DIR", str(embedding))
    if thresholds.is_file():
        os.environ.setdefault("SEMANTIC_THRESHOLDS_PATH", str(thresholds))

    load_thresholds(thresholds if thresholds.is_file() else None)

    fallback = SyncResult(
        version="local",
        local_dir=root,
        intent_model_path=intent if intent.is_file() else None,
        embedding_model_dir=embedding if embedding.is_dir() else None,
    )
    apply_bundle(fallback)


def _require_paths() -> None:
    errors: list[str] = []
    path = os.getenv("INTENT_MODEL_PATH", "").strip()
    if not path or not Path(path).is_file():
        errors.append(f"intent model missing: {path or '<unset>'}")

    path = os.getenv("EMBEDDING_MODEL_DIR", "").strip()
    if not path or not Path(path).is_dir():
        errors.append(f"embedding model dir missing: {path or '<unset>'}")

    thresholds = os.getenv("SEMANTIC_THRESHOLDS_PATH", "").strip()
    if not thresholds or not Path(thresholds).is_file():
        errors.append(f"semantic thresholds missing: {thresholds or '<unset>'}")

    if errors:
        for err in errors:
            logger.error(err)
        raise RuntimeError("model bootstrap failed")


def bootstrap_models() -> None:
    from app.env import load_project_env

    load_project_env()

    synced_from_s3 = False
    try:
        if should_sync_models():
            try:
                result = sync_models_from_s3()
                if result is None:
                    raise RuntimeError("expected S3 model sync but got no result")
                synced_from_s3 = True
                apply_bundle(result)
                logger.info("Model bundle %s ready at %s", result.version, result.local_dir)
            except Exception as exc:
                local = find_local_bundle(_local_models_dir())
                if local is None:
                    raise
                logger.warning(
                    "S3 model sync failed (%s), using local bundle %s at %s",
                    exc,
                    local.version,
                    local.local_dir,
                )
                apply_bundle(local)
        else:
            _apply_local_defaults()

        if synced_from_s3:
            _require_paths()
    except Exception:
        logger.exception("Model bootstrap failed")
        sys.exit(1)
