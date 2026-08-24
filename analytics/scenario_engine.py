"""Deterministic marketing budget scenario calculations.

All outputs are simulations derived from explicit assumptions. The module does
not approve budgets or estimate causal lift.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ScenarioInputs:
    total_budget: float
    channel_allocations: Mapping[str, float]
    cpc: float
    conversion_rate: float
    aov: float
    target_roas: float
    target_cac: float
    growth_assumption: float = 0.0
    click_to_session_rate: float = 0.9
    customer_rate: float = 1.0


@dataclass(frozen=True)
class ScenarioAdjustment:
    budget_multiplier: float = 1.0
    cpc_multiplier: float = 1.0
    conversion_multiplier: float = 1.0
    aov_multiplier: float = 1.0


SCENARIO_ADJUSTMENTS = {
    "Baseline": ScenarioAdjustment(),
    "Conservative": ScenarioAdjustment(
        budget_multiplier=0.9,
        cpc_multiplier=1.05,
        conversion_multiplier=0.9,
        aov_multiplier=0.95,
    ),
    "Expected": ScenarioAdjustment(),
    "Aggressive": ScenarioAdjustment(
        budget_multiplier=1.2,
        cpc_multiplier=1.1,
        conversion_multiplier=1.1,
        aov_multiplier=1.05,
    ),
}


def _validate(inputs: ScenarioInputs) -> None:
    if inputs.total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    if inputs.cpc <= 0:
        raise ValueError("cpc must be greater than zero")
    if inputs.aov < 0 or inputs.target_roas < 0 or inputs.target_cac < 0:
        raise ValueError("aov and targets must be non-negative")
    for name, value in {
        "conversion_rate": inputs.conversion_rate,
        "click_to_session_rate": inputs.click_to_session_rate,
        "customer_rate": inputs.customer_rate,
    }.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between zero and one")
    if not inputs.channel_allocations:
        raise ValueError("at least one channel allocation is required")
    if any(value < 0 for value in inputs.channel_allocations.values()):
        raise ValueError("channel allocations must be non-negative")
    if abs(sum(inputs.channel_allocations.values()) - 1.0) > 1e-6:
        raise ValueError("channel allocations must sum to 1.0")


def run_scenario(
    inputs: ScenarioInputs,
    scenario_name: str,
    adjustment: ScenarioAdjustment | None = None,
) -> list[dict[str, float | str]]:
    """Return channel-level simulation rows for a named scenario."""
    _validate(inputs)
    if scenario_name == "User Defined":
        selected = adjustment or ScenarioAdjustment()
    else:
        if adjustment is not None:
            raise ValueError("custom adjustment is supported only for User Defined")
        try:
            selected = SCENARIO_ADJUSTMENTS[scenario_name]
        except KeyError as exc:
            raise ValueError(f"unsupported scenario: {scenario_name}") from exc

    growth_factor = 1 + inputs.growth_assumption if scenario_name in {"Expected", "Aggressive"} else 1.0
    effective_budget = inputs.total_budget * selected.budget_multiplier
    effective_cpc = inputs.cpc * selected.cpc_multiplier
    effective_conversion_rate = min(1.0, inputs.conversion_rate * selected.conversion_multiplier * growth_factor)
    effective_aov = inputs.aov * selected.aov_multiplier * growth_factor
    rows: list[dict[str, float | str]] = []

    for channel, allocation in inputs.channel_allocations.items():
        channel_budget = effective_budget * allocation
        projected_clicks = channel_budget / effective_cpc
        projected_sessions = projected_clicks * inputs.click_to_session_rate
        projected_conversions = projected_sessions * effective_conversion_rate
        projected_customers = projected_conversions * inputs.customer_rate
        projected_revenue = projected_customers * effective_aov
        projected_cac = channel_budget / projected_customers if projected_customers else 0.0
        projected_roas = projected_revenue / channel_budget if channel_budget else 0.0
        rows.append(
            {
                "scenario_name": scenario_name,
                "channel": channel,
                "simulation_status": "SIMULATED",
                "total_budget": round(effective_budget, 2),
                "channel_allocation": allocation,
                "channel_budget": round(channel_budget, 2),
                "cpc_assumption": round(effective_cpc, 4),
                "conversion_assumption": round(effective_conversion_rate, 6),
                "aov_assumption": round(effective_aov, 2),
                "projected_clicks": round(projected_clicks, 2),
                "projected_sessions": round(projected_sessions, 2),
                "projected_conversions": round(projected_conversions, 2),
                "projected_customers": round(projected_customers, 2),
                "projected_revenue": round(projected_revenue, 2),
                "projected_cac": round(projected_cac, 2),
                "projected_roas": round(projected_roas, 4),
                "target_roas": inputs.target_roas,
                "target_cac": inputs.target_cac,
                "roas_target_variance": round(projected_roas - inputs.target_roas, 4),
                "cac_target_variance": round(projected_cac - inputs.target_cac, 2),
                "growth_assumption": inputs.growth_assumption,
                "methodology": "deterministic_budget_funnel_simulation",
            }
        )
    return rows


def run_standard_scenarios(
    inputs: ScenarioInputs,
    user_defined: ScenarioAdjustment | None = None,
) -> list[dict[str, float | str]]:
    """Run the four governed presets and an optional user-defined scenario."""
    rows: list[dict[str, float | str]] = []
    for scenario_name in SCENARIO_ADJUSTMENTS:
        rows.extend(run_scenario(inputs, scenario_name))
    if user_defined is not None:
        rows.extend(run_scenario(inputs, "User Defined", user_defined))
    return rows


def scenario_contract() -> dict[str, object]:
    return {
        "input_fields": list(asdict(ScenarioInputs(0, {"channel": 1.0}, 1, 0, 0, 0, 0)).keys()),
        "scenarios": [*SCENARIO_ADJUSTMENTS, "User Defined"],
        "output_classification": "SIMULATED",
        "limitation": "Planning simulation only; not causal lift or an approved budget.",
    }
