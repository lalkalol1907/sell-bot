#!/usr/bin/env python3
"""Build and publish matching model bundle to S3-compatible storage."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
EMBEDDING_SUBDIR = Path("embedding") / "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
ONNX_FILENAMES = ("model.onnx", "model_optimized.onnx")


def _find_onnx_model_dir(root: Path, *, model_hint: str) -> Path | None:
    hint = model_hint.lower().replace("/", "-")
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name not in ONNX_FILENAMES:
            continue
        normalized = str(path).lower()
        if hint in normalized or "paraphrase-multilingual-minilm-l12-v2" in normalized:
            return path.parent
    return None


def _resolve_fastembed_model_source(model_name: str) -> Path:
    from fastembed import TextEmbedding

    embedding = TextEmbedding(model_name=model_name)
    list(embedding.embed(["warmup"]))

    cache_dir = getattr(getattr(embedding, "model", None), "cache_dir", None)
    if cache_dir:
        source = _find_onnx_model_dir(Path(cache_dir), model_hint=model_name)
        if source is not None:
            return source

    legacy_root = Path.home() / ".cache" / "fastembed"
    if legacy_root.is_dir():
        source = _find_onnx_model_dir(legacy_root, model_hint=model_name)
        if source is not None:
            return source

    raise RuntimeError(
        f"Could not locate ONNX files for {model_name}. "
        "Run once with network access so fastembed can download the model."
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collect_files(bundle_dir: Path) -> list[dict]:
    files = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle_dir).as_posix()
        files.append(
            {
                "path": rel,
                "sha256": _sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return files


def _prepare_embedding_dir(target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    source_dir = _resolve_fastembed_model_source(MODEL_NAME)
    shutil.copytree(source_dir, target)


def _copy_intent_artifacts(bundle_dir: Path) -> None:
    for pattern in ("intent_v*.joblib", "intent_v*.meta.json", "semantic_thresholds.json"):
        for src in MODELS.glob(pattern):
            shutil.copy2(src, bundle_dir / src.name)


def _run_parity_check(embedding_dir: Path, max_drift: float) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "verify_embedding_parity.py"),
        "--model-dir",
        str(embedding_dir),
        "--max-drift",
        str(max_drift),
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("embedding parity check failed")


def _s3_client():
    import os

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


def _upload_bundle(bundle_dir: Path, version: str, *, update_latest: bool) -> None:
    import os

    bucket = os.getenv("MODELS_S3_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError("MODELS_S3_BUCKET is required for upload")

    prefix = os.getenv("MODELS_S3_PREFIX", "").strip()
    client = _s3_client()

    for path in bundle_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle_dir).as_posix()
        key = _object_key(prefix, version, rel)
        client.upload_file(str(path), bucket, key)

    if update_latest:
        payload = json.dumps({"version": version}, ensure_ascii=False).encode("utf-8")
        client.put_object(Bucket=bucket, Key=_latest_key(prefix), Body=payload, ContentType="application/json")


def build_bundle(version: str, *, skip_parity: bool, max_drift: float) -> Path:
    staging = ROOT / ".bundle-staging" / version
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    embedding_dir = staging / EMBEDDING_SUBDIR
    _prepare_embedding_dir(embedding_dir)
    _copy_intent_artifacts(staging)

    if not skip_parity:
        _run_parity_check(embedding_dir, max_drift)

    manifest = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "embedding_format": "onnx-fastembed-v1",
        "embedding_model": MODEL_NAME,
        "files": _collect_files(staging),
    }
    (staging / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return staging


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Build bundle under models/bundles/<version> (upload via scripts/publish_models.sh)",
    )
    parser.add_argument("--skip-parity", action="store_true")
    parser.add_argument("--max-drift", type=float, default=0.02)
    parser.add_argument("--no-latest", action="store_true")
    args = parser.parse_args()

    bundle_dir = build_bundle(args.version, skip_parity=args.skip_parity, max_drift=args.max_drift)

    if args.local_only:
        target = MODELS / "bundles" / args.version
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(bundle_dir, target)
        print(f"Local bundle: {target}")
        return 0

    _upload_bundle(bundle_dir, args.version, update_latest=not args.no_latest)
    print(f"Published bundle {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
