"""Background polling for S3 model bundle updates."""

from __future__ import annotations

import logging
import os
import threading
import time

from app.env import bool_env
from app.models_runtime import reload_if_changed
from app.models_sync import should_sync_models

logger = logging.getLogger(__name__)


def should_watch_models() -> bool:
    if os.getenv("MODELS_S3_VERSION", "").strip():
        return False
    if not should_sync_models():
        return False

    raw = os.getenv("MODELS_WATCH_ENABLED", "").strip()
    if raw:
        return bool_env("MODELS_WATCH_ENABLED", default=False)
    return True


def watch_interval_seconds() -> int:
    raw = os.getenv("MODELS_WATCH_INTERVAL", "60").strip()
    try:
        interval = int(raw)
    except ValueError:
        interval = 60
    return max(interval, 5)


def _watch_loop() -> None:
    interval = watch_interval_seconds()
    logger.info("Model watcher started (interval=%ss)", interval)
    while True:
        time.sleep(interval)
        try:
            if reload_if_changed():
                logger.info("Model bundle reloaded via watcher")
        except Exception:
            logger.exception("Model watcher tick failed")


def start_models_watcher() -> None:
    if not should_watch_models():
        logger.info("Model watcher disabled")
        return
    thread = threading.Thread(target=_watch_loop, name="models-watcher", daemon=True)
    thread.start()
