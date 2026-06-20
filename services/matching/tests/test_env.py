"""Tests for monorepo .env loading."""

from __future__ import annotations

import os

from app.env import find_monorepo_dotenv, load_dotenv_file, load_project_env


def test_load_dotenv_file_respects_existing_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MODELS_S3_BUCKET=from-file\nMODELS_S3_PREFIX=prefix/\n", encoding="utf-8")
    monkeypatch.setenv("MODELS_S3_BUCKET", "from-shell")

    load_dotenv_file(env_file)

    assert os.environ["MODELS_S3_BUCKET"] == "from-shell"
    assert os.environ["MODELS_S3_PREFIX"] == "prefix/"


def test_find_monorepo_dotenv_from_repo_root(tmp_path, monkeypatch):
    (tmp_path / "docker-compose.yml").write_text("services:\n", encoding="utf-8")
    (tmp_path / ".env").write_text("MODELS_S3_BUCKET=sellbot\n", encoding="utf-8")
    matching = tmp_path / "services" / "matching"
    matching.mkdir(parents=True)

    monkeypatch.chdir(matching)

    assert find_monorepo_dotenv() == tmp_path / ".env"


def test_load_project_env(tmp_path, monkeypatch):
    (tmp_path / "docker-compose.yml").write_text("services:\n", encoding="utf-8")
    (tmp_path / ".env").write_text("MODELS_S3_BUCKET=sellbot\n", encoding="utf-8")
    matching = tmp_path / "services" / "matching"
    matching.mkdir(parents=True)
    monkeypatch.chdir(matching)
    monkeypatch.delenv("MODELS_S3_BUCKET", raising=False)

    loaded = load_project_env()

    assert loaded == tmp_path / ".env"
    assert os.environ["MODELS_S3_BUCKET"] == "sellbot"
