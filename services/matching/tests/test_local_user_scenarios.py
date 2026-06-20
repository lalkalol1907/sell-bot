"""Local user scenario tests — run manually, excluded from CI."""

from __future__ import annotations

import pytest

from app.local_scenarios_harness import (
    assert_scenario,
    load_local_dataset,
    run_scenario,
)

CATALOG, SCENARIOS = load_local_dataset()


@pytest.mark.local
def test_local_dataset_has_catalog_and_scenarios():
    assert len(CATALOG) >= 10
    assert len(SCENARIOS) >= 40


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
@pytest.mark.local
def test_local_user_scenario(scenario):
    actual = run_scenario(scenario)
    errors = assert_scenario(scenario, actual)
    assert not errors, f"{scenario.id}: " + "; ".join(errors)
