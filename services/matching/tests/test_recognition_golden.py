"""Golden regression tests from recognition_cases.yaml."""

from __future__ import annotations

import pytest

from app.recognition_harness import assert_case, load_cases, run_case

CASES = load_cases()
FAST_CASES = [c for c in CASES if not c.requires_semantic]
SEMANTIC_CASES = [c for c in CASES if c.requires_semantic]


@pytest.mark.parametrize("case", FAST_CASES, ids=lambda c: c.id)
def test_recognition_golden_fast(case):
    actual = run_case(case)
    errors = assert_case(case, actual)
    assert not errors, f"{case.id}: " + "; ".join(errors)


@pytest.mark.parametrize("case", SEMANTIC_CASES, ids=lambda c: c.id)
@pytest.mark.integration
def test_recognition_golden_semantic(case):
    actual = run_case(case)
    errors = assert_case(case, actual)
    assert not errors, f"{case.id}: " + "; ".join(errors)


def test_golden_suite_has_minimum_cases():
    assert len(CASES) >= 80
