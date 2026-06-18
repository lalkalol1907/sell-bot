"""Download versioned model bundles from S3-compatible storage."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

EMBEDDING_SUBDIR = Path("embedding") / "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class SyncResult:
    version: str
    local_dir: Path
    intent_model_path: Path | None
    embedding_model_dir: Path | None


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def should_sync_models() -> bool:
    if _bool_env("MODELS_SKIP_S3"):
        return False
    if not os.getenv("MODELS_S3_BUCKET", "").strip():
        return False
    semantic = _bool_env("NLP_V2_SEMANTIC", True)
    intent_ml = _bool_env("NLP_V2_INTENT_ML", True)
    return semantic or intent_ml


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


def _resolve_version(client, bucket: str, prefix: str) -> str:
    pinned = os.getenv("MODELS_S3_VERSION", "").strip()
    if pinned:
        return pinned

    response = client.get_object(Bucket=bucket, Key=_latest_key(prefix))
    payload = json.loads(response["Body"].read().decode("utf-8"))
    version = payload.get("version")
    if not version:
        raise RuntimeError("latest.json missing version field")
    return str(version)


def _download_bundle(client, bucket: str, prefix: str, version: str, local_dir: Path) -> SyncResult:
    manifest_key = _object_key(prefix, version, "manifest.json")
    response = client.get_object(Bucket=bucket, Key=manifest_key)
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

    intent_path = active / "intent_v1.joblib"
    embedding_dir = active / EMBEDDING_SUBDIR
    return SyncResult(
        version=version,
        local_dir=active,
        intent_model_path=intent_path if intent_path.is_file() else None,
        embedding_model_dir=embedding_dir if embedding_dir.is_dir() else None,
    )


def sync_models_from_s3() -> SyncResult | None:
    if not should_sync_models():
        logger.info("Skipping S3 model sync")
        return None

    bucket = os.getenv("MODELS_S3_BUCKET", "").strip()
    prefix = os.getenv("MODELS_S3_PREFIX", "").strip()
    local_dir = Path(os.getenv("MODELS_LOCAL_DIR", "/data/models"))

    client = _s3_client()
    version = _resolve_version(client, bucket, prefix)
    logger.info("Syncing model bundle %s from s3://%s/%s", version, bucket, prefix or "")
    local_dir.mkdir(parents=True, exist_ok=True)
    return _download_bundle(client, bucket, prefix, version, local_dir)
