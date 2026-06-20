"""Shared environment helpers."""

from __future__ import annotations

import os
from pathlib import Path


def bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[7:].strip()
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return key, value


def load_dotenv_file(path: Path, *, override: bool = False) -> None:
    """Load KEY=VALUE pairs from a .env file."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_dotenv_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value


def find_monorepo_dotenv() -> Path | None:
    """Return repo-root .env (next to docker-compose.yml) if present."""
    from app.paths import project_root

    for start in (Path.cwd().resolve(), project_root().resolve()):
        current = start
        for _ in range(8):
            if (current / "docker-compose.yml").is_file():
                env_path = current / ".env"
                return env_path if env_path.is_file() else None
            parent = current.parent
            if parent == current:
                break
            current = parent
    return None


def load_project_env() -> Path | None:
    """Load monorepo .env for local CLI/bootstrap (does not override existing env)."""
    env_path = find_monorepo_dotenv()
    if env_path is not None:
        load_dotenv_file(env_path)
    return env_path
