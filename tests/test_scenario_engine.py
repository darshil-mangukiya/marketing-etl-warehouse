import pytest

from analytics.scenario_engine import (
    ScenarioAdjustment,
    ScenarioInputs,
    run_scenario,
    run_standard_scenarios,
)


def _inputs() -> ScenarioInputs:
    return ScenarioInputs(
        total_budget=100_000,
        channel_allocations={"paid_search": 0.6, "paid_social": 0.4},
        cpc=2.0,
        conversion_rate=0.04,
        aov=150.0,
        target_roas=2.5,
        target_cac=80.0,
        growth_assumption=0.05,
    )


def test_standard_scenarios_are_labeled_and_reconcile_budget() -> None:
    rows = run_standard_scenarios(_inputs())

    assert {row["scenario_name"] for row in rows} == {"Baseline", "Conservative", "Expected", "Aggressive"}
    assert all(row["simulation_status"] == "SIMULATED" for row in rows)
    baseline = [row for row in rows if row["scenario_name"] == "Baseline"]
    assert sum(row["channel_budget"] for row in baseline) == 100_000
    assert all(row["projected_roas"] > 0 for row in rows)


def test_user_defined_scenario_uses_explicit_adjustment() -> None:
    rows = run_scenario(
        _inputs(),
        "User Defined",
        ScenarioAdjustment(budget_multiplier=1.1, cpc_multiplier=0.95, conversion_multiplier=1.05),
    )

    assert sum(row["channel_budget"] for row in rows) == 110_000
    assert {row["scenario_name"] for row in rows} == {"User Defined"}


def test_scenario_rejects_invalid_allocation() -> None:
    invalid = ScenarioInputs(100, {"paid_search": 0.8}, 2, 0.04, 150, 2, 80)

    with pytest.raises(ValueError, match="sum to 1.0"):
        run_scenario(invalid, "Baseline")
