"""Build and publish matching model bundle to S3-compatible storage."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.config import INTENT_META_NAME, INTENT_MODEL_NAME, THRESHOLDS_NAME
from app.paths import models_dir
from app.training.parity import MODEL_HINT, MODEL_NAME, ONNX_FILENAMES, check_parity

EMBEDDING_SUBDIR = Path("embedding") / "paraphrase-multilingual-MiniLM-L12-v2"


def _onnx_model_path(model_dir: Path) -> Path | None:
    for name in ONNX_FILENAMES:
        candidate = model_dir / name
        if candidate.is_file():
            return candidate
    return None


def _is_valid_embedding_dir(path: Path) -> bool:
    return path.is_dir() and _onnx_model_path(path) is not None


def _find_onnx_model_dir(root: Path, *, model_hint: str) -> Path | None:
    hint = model_hint.lower().replace("/", "-")
    for path in sorted(root.rglob("*")):
        if path.name not in ONNX_FILENAMES:
            continue
        if not path.is_file():
            continue
        normalized = str(path).lower()
        if hint in normalized or MODEL_HINT in normalized:
            return path.parent
    return None


def _fastembed_cache_roots() -> list[Path]:
    from app.training.parity import fastembed_cache_roots

    return fastembed_cache_roots()


def _local_embedding_sources(models_root: Path) -> list[Path]:
    sources: list[Path] = []

    direct = models_root / EMBEDDING_SUBDIR
    if direct.is_dir():
        sources.append(direct)

    bundles_root = models_root / "bundles"
    if bundles_root.is_dir():
        for bundle in sorted(bundles_root.iterdir(), reverse=True):
            candidate = bundle / EMBEDDING_SUBDIR
            if candidate.is_dir():
                sources.append(candidate)

    for cache_root in _fastembed_cache_roots():
        found = _find_onnx_model_dir(cache_root, model_hint=MODEL_NAME)
        if found is not None:
            sources.append(found)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for source in sources:
        resolved = source.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return deduped


def _clear_broken_fastembed_caches(model_name: str) -> list[Path]:
    hint = model_name.lower().replace("/", "-")
    removed: list[Path] = []
    for cache_root in _fastembed_cache_roots():
        if not cache_root.is_dir():
            continue
        for path in cache_root.iterdir():
            normalized = path.name.lower()
            if hint not in normalized and MODEL_HINT not in normalized:
                continue
            if _is_valid_embedding_dir(path):
                continue
            found = _find_onnx_model_dir(path, model_hint=model_name)
            if found is not None and _is_valid_embedding_dir(found):
                continue
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path)
    return removed


def _download_fastembed_model(model_name: str) -> Path:
    from fastembed import TextEmbedding

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            embedding = TextEmbedding(model_name=model_name)
            list(embedding.embed(["warmup"]))

            cache_dir = getattr(getattr(embedding, "model", None), "cache_dir", None)
            if cache_dir:
                source = _find_onnx_model_dir(Path(cache_dir), model_hint=model_name)
                if source is not None and _is_valid_embedding_dir(source):
                    return source.resolve()

            for cache_root in _fastembed_cache_roots():
                source = _find_onnx_model_dir(cache_root, model_hint=model_name)
                if source is not None and _is_valid_embedding_dir(source):
                    return source.resolve()

            raise RuntimeError(f"fastembed loaded {model_name} but ONNX files were not found")
        except Exception as exc:
            last_error = exc
            if attempt == 0 and _clear_broken_fastembed_caches(model_name):
                continue
            break

    assert last_error is not None
    raise RuntimeError(
        f"Could not download ONNX files for {model_name}: {last_error}. "
        "Delete the broken fastembed cache and retry with network access."
    ) from last_error


def resolve_fastembed_model_source(model_name: str = MODEL_NAME, *, models_root: Path | None = None) -> Path:
    root = models_root or models_dir()
    for source in _local_embedding_sources(root):
        if _is_valid_embedding_dir(source):
            print(f"Using local embedding model: {source}", file=sys.stderr)
            return source

    print(f"Downloading embedding model via fastembed: {model_name}", file=sys.stderr)
    return _download_fastembed_model(model_name)


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

    source_dir = resolve_fastembed_model_source()
    shutil.copytree(source_dir, target)


def _copy_intent_artifacts(bundle_dir: Path, models_root: Path) -> None:
    for name in (INTENT_MODEL_NAME, INTENT_META_NAME, THRESHOLDS_NAME):
        src = models_root / name
        if not src.is_file():
            raise RuntimeError(f"Missing required artifact: {src}")
        shutil.copy2(src, bundle_dir / name)


def validate_artifacts(models_root: Path | None = None) -> None:
    root = models_root or models_dir()
    errors: list[str] = []
    for name in (INTENT_MODEL_NAME, THRESHOLDS_NAME):
        if not (root / name).is_file():
            errors.append(f"missing {name}")

    embedding = root / EMBEDDING_SUBDIR
    if not _is_valid_embedding_dir(embedding):
        try:
            resolve_fastembed_model_source(models_root=root)
        except Exception as exc:
            errors.append(f"embedding model unavailable: {exc}")

    if errors:
        raise RuntimeError("publish validation failed: " + "; ".join(errors))


def run_golden_gate() -> None:
    from app.recognition_harness import assert_case, load_cases, run_case

    failures: list[str] = []
    for case in load_cases():
        actual = run_case(case)
        errors = assert_case(case, actual)
        if errors:
            failures.append(f"{case.id}: " + "; ".join(errors))

    if failures:
        raise RuntimeError(
            f"golden recognition suite failed ({len(failures)} cases):\n"
            + "\n".join(failures[:20])
        )


def build_bundle(version: str, *, max_drift: float = 0.02, models_root: Path | None = None) -> Path:
    root = models_root or models_dir()
    validate_artifacts(root)

    staging = Path(tempfile.mkdtemp(prefix=f"matching-bundle-{version}-"))
    try:
        embedding_dir = staging / EMBEDDING_SUBDIR
        _prepare_embedding_dir(embedding_dir)
        _copy_intent_artifacts(staging, root)

        report = check_parity(embedding_dir, max_drift=max_drift)
        print(report, file=sys.stderr)
        if not report["passed"]:
            raise RuntimeError("embedding parity check failed")

        run_golden_gate()

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
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


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


def upload_bundle(bundle_dir: Path, version: str, *, update_latest: bool = True) -> None:
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


def copy_local_bundle(bundle_dir: Path, version: str, models_root: Path | None = None) -> Path:
    root = models_root or models_dir()
    target = root / "bundles" / version
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle_dir, target)
    return target


def publish(version: str, *, max_drift: float = 0.02, update_latest: bool = True) -> Path:
    bundle_dir = build_bundle(version, max_drift=max_drift)
    try:
        upload_bundle(bundle_dir, version, update_latest=update_latest)
        local = copy_local_bundle(bundle_dir, version)
        print(f"Published bundle {version} to S3; local copy at {local}")
        return local
    finally:
        shutil.rmtree(bundle_dir, ignore_errors=True)
