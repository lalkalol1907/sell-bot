"""Download versioned model bundles from S3-compatible storage."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.config import INTENT_MODEL_NAME, THRESHOLDS_NAME, should_sync_models
from app.env import bool_env

logger = logging.getLogger(__name__)

EMBEDDING_SUBDIR = Path("embedding") / "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class SyncResult:
    version: str
    local_dir: Path
    intent_model_path: Path | None
    embedding_model_dir: Path | None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_up_to_date(path: Path, expected_sha: str, expected_size: int) -> bool:
    if not path.is_file():
        return False
    if path.stat().st_size != expected_size:
        return False
    return _sha256_file(path) == expected_sha


def _s3_client():
    import boto3
    from botocore.config import Config

    endpoint = os.getenv("MODELS_S3_ENDPOINT", "").strip() or None
    region = os.getenv("MODELS_S3_REGION", "").strip() or None
    access_key = os.getenv("MODELS_S3_ACCESS_KEY", "").strip() or None
    secret_key = os.getenv("MODELS_S3_SECRET_KEY", "").strip() or None

    session_kwargs: dict = {}
    if access_key and secret_key:
        session_kwargs["aws_access_key_id"] = access_key
        session_kwargs["aws_secret_access_key"] = secret_key

    session = boto3.session.Session(**session_kwargs)
    return session.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )


def _object_key(prefix: str, version: str, relative: str) -> str:
    prefix = prefix.strip("/")
    relative = relative.lstrip("/")
    return f"{prefix}/matching/{version}/{relative}" if prefix else f"matching/{version}/{relative}"


def _latest_key(prefix: str) -> str:
    prefix = prefix.strip("/")
    return f"{prefix}/matching/latest.json" if prefix else "matching/latest.json"


def s3_uri(bucket: str, key: str) -> str:
    return f"s3://{bucket}/{key}"


def _get_object(client, bucket: str, key: str) -> dict:
    try:
        return client.get_object(Bucket=bucket, Key=key)
    except Exception as exc:
        code = ""
        if hasattr(exc, "response"):
            code = exc.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404", "NotFound"):
            raise RuntimeError(
                f"S3 object not found: {s3_uri(bucket, key)} "
                f"(publish with: make publish MODELS_VERSION=<version>)"
            ) from exc
        raise


def _bundle_from_dir(bundle_dir: Path, version: str) -> SyncResult | None:
    intent_path = bundle_dir / INTENT_MODEL_NAME
    embedding_dir = bundle_dir / EMBEDDING_SUBDIR
    has_intent = intent_path.is_file()
    has_embedding = embedding_dir.is_dir()
    if not has_intent and not has_embedding:
        return None
    return SyncResult(
        version=version,
        local_dir=bundle_dir,
        intent_model_path=intent_path if has_intent else None,
        embedding_model_dir=embedding_dir if has_embedding else None,
    )


def find_local_bundle(local_dir: Path) -> SyncResult | None:
    """Find model artifacts under local_dir (flat or versioned bundle layout)."""
    root = Path(local_dir)
    flat = _bundle_from_dir(root, "local")
    if flat is not None:
        return flat

    if not root.is_dir():
        return None

    candidates: list[tuple[str, Path]] = []
    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / "manifest.json").is_file() or (child / INTENT_MODEL_NAME).is_file():
            candidates.append((child.name, child))

    for version, bundle_dir in sorted(candidates, key=lambda item: item[0], reverse=True):
        bundle = _bundle_from_dir(bundle_dir, version)
        if bundle is not None:
            return bundle
    return None


def _resolve_version(client, bucket: str, prefix: str) -> str:
    pinned = os.getenv("MODELS_S3_VERSION", "").strip()
    if pinned:
        return pinned

    latest_key = _latest_key(prefix)
    response = _get_object(client, bucket, latest_key)
    payload = json.loads(response["Body"].read().decode("utf-8"))
    version = payload.get("version")
    if not version:
        raise RuntimeError("latest.json missing version field")
    return str(version)


def _download_bundle(client, bucket: str, prefix: str, version: str, local_dir: Path) -> SyncResult:
    manifest_key = _object_key(prefix, version, "manifest.json")
    response = _get_object(client, bucket, manifest_key)
    manifest = json.loads(response["Body"].read().decode("utf-8"))

    staging = local_dir / ".staging" / version
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    for entry in manifest.get("files", []):
        rel_path = entry["path"]
        dest = staging / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and _file_up_to_date(dest, entry["sha256"], int(entry["size"])):
            continue
        key = _object_key(prefix, version, rel_path)
        client.download_file(bucket, key, str(dest))
        actual = _sha256_file(dest)
        if actual != entry["sha256"]:
            raise RuntimeError(f"checksum mismatch for {rel_path}: expected {entry['sha256']}, got {actual}")

    active = local_dir / version
    if active.exists():
        shutil.rmtree(active)
    staging.rename(active)

    intent_path = active / INTENT_MODEL_NAME
    embedding_dir = active / EMBEDDING_SUBDIR
    return SyncResult(
        version=version,
        local_dir=active,
        intent_model_path=intent_path if intent_path.is_file() else None,
        embedding_model_dir=embedding_dir if embedding_dir.is_dir() else None,
    )


def peek_remote_version() -> str | None:
    if not should_sync_models():
        return None

    bucket = os.getenv("MODELS_S3_BUCKET", "").strip()
    prefix = os.getenv("MODELS_S3_PREFIX", "").strip()
    client = _s3_client()
    return _resolve_version(client, bucket, prefix)


def sync_models_from_s3(version: str | None = None) -> SyncResult | None:
    if not should_sync_models():
        logger.info("Skipping S3 model sync")
        return None

    bucket = os.getenv("MODELS_S3_BUCKET", "").strip()
    prefix = os.getenv("MODELS_S3_PREFIX", "").strip()
    local_dir = Path(os.getenv("MODELS_LOCAL_DIR", "/data/models"))

    client = _s3_client()
    resolved = version or _resolve_version(client, bucket, prefix)
    logger.info("Syncing model bundle %s from s3://%s/%s", resolved, bucket, prefix or "")
    local_dir.mkdir(parents=True, exist_ok=True)
    return _download_bundle(client, bucket, prefix, resolved, local_dir)
