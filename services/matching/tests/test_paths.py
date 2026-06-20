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


def test_dataset_seed_files_loadable():
    from app.training.datasets import (
        load_intent_samples,
        load_product_catalog_keywords,
        load_product_pairs_seed,
    )
    from app.training.parity import load_sample_texts

    samples = load_intent_samples()
    keywords = load_product_catalog_keywords()
    _, pairs = load_product_pairs_seed()
    parity = load_sample_texts()

    assert len(samples["buy"]) >= 20
    assert len(keywords) >= 10
    assert len(pairs) >= 60
    assert len(parity) >= 15


def test_translit_pairs_loadable():
    from app.nlp.normalize import translit_expand

    expanded = translit_expand("айфон")
    assert expanded
