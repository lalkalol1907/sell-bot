"""Tests for project path resolution (pip install + CI cwd)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_project_root_uses_cwd_when_installed():
    from app.paths import data_dir, project_root

    root = project_root()
    cases = data_dir() / "recognition_cases.yaml"
    assert cases.is_file(), f"missing {cases} (root={root})"
    assert root == ROOT.resolve()


def test_recognition_cases_loadable():
    from app.recognition_harness import load_cases

    cases = load_cases()
    assert len(cases) >= 80


def test_translit_pairs_loadable():
    from app.nlp.normalize import translit_expand

    expanded = translit_expand("айфон")
    assert expanded
