import pandas as pd

from scripts.build_demo_marts import (
    _action_center,
    _budget_scenarios,
    _data_product_scorecard,
    _performance_forecast,
    _semantic_kpi_governance,
)


def test_performance_forecast_generates_three_month_horizon() -> None:
    channel_perf = pd.DataFrame(
        {
            "reporting_month": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
            "normalized_channel": ["paid_search", "paid_search", "paid_search"],
            "spend": [1000, 1200, 1400],
            "booked_revenue": [3000, 3600, 4200],
            "gross_margin": [1500, 1800, 2100],
            "leads": [100, 110, 120],
            "closed_won_conversions": [10, 12, 14],
        }
    )

    forecast = _performance_forecast(channel_perf)

    assert len(forecast) == 3
    assert forecast["forecast_horizon_months"].tolist() == [1, 2, 3]
    assert forecast["forecast_month"].min() > channel_perf["reporting_month"].max()
    assert (forecast["forecast_roas"] > 0).all()


def test_budget_scenarios_includes_recommended_mix() -> None:
    channel_perf = pd.DataFrame(
        {
            "normalized_channel": ["paid_search"],
            "spend": [1000],
            "booked_revenue": [4000],
            "gross_margin": [2200],
            "leads": [100],
            "closed_won_conversions": [10],
        }
    )
    campaign_optimization = pd.DataFrame(
        {
            "normalized_channel": ["paid_search"],
            "spend": [1000],
            "recommended_monthly_budget": [1200],
        }
    )

    scenarios = _budget_scenarios(channel_perf, campaign_optimization)

    assert {"baseline", "conservative_cut", "recommended_mix", "aggressive_growth"} == set(scenarios["scenario_name"])
    recommended = scenarios[scenarios["scenario_name"].eq("recommended_mix")].iloc[0]
    assert recommended["budget_shift_pct"] == 0.2
    assert recommended["projected_revenue"] > 0


def test_action_center_prioritizes_operational_work() -> None:
    campaign_optimization = pd.DataFrame(
        {
            "campaign_name": ["Search Brand"],
            "normalized_channel": ["paid_search"],
            "recommended_action": ["reduce"],
            "spend": [5000],
            "recommended_monthly_budget": [3750],
            "attributed_roas": [0.8],
            "opportunity_score": [1.0],
            "optimization_reason": ["High spend is not producing enough attributed revenue."],
        }
    )
    budget_pacing = pd.DataFrame(
        {
            "channel": ["paid_search"],
            "budget_owner": ["growth"],
            "pacing_status": ["under_pacing"],
            "revenue_gap": [10000],
            "revenue_attainment": [0.55],
        }
    )
    marketing_anomalies = pd.DataFrame(
        {
            "severity": ["high"],
            "metric_name": ["spend"],
            "normalized_channel": ["paid_search"],
            "investigation_hint": ["Spend increase needs review."],
            "pct_change": [0.9],
            "z_score": [2.4],
        }
    )
    source_health = pd.DataFrame(
        {
            "source_system": ["google_ads"],
            "source_health_status": ["attention"],
            "rejected": [10],
            "quality_issue_count": [2],
            "acceptance_rate": [0.98],
            "rejection_rate": [0.02],
        }
    )
    data_quality = pd.DataFrame(
        {
            "source_system": ["google_ads"],
            "monitoring_status": ["quality_warning"],
            "issue_count": [3],
            "rejected_rate": [0.03],
        }
    )
    budget_scenarios = pd.DataFrame(
        {
            "decision": ["approve"],
            "scenario_name": ["recommended_mix"],
            "normalized_channel": ["paid_search"],
            "incremental_margin": [2000],
            "projected_roas": [3.5],
            "scenario_note": ["Apply recommendations."],
        }
    )
    performance_forecast = pd.DataFrame(
        {
            "normalized_channel": ["paid_search"],
            "forecast_roas": [0.8],
            "forecast_cac": [500],
            "forecast_spend": [1000],
            "forecast_horizon_months": [1],
        }
    )

    action_center = _action_center(
        campaign_optimization,
        budget_pacing,
        marketing_anomalies,
        source_health,
        data_quality,
        budget_scenarios,
        performance_forecast,
    )

    assert action_center["action_id"].str.startswith("ACT-").all()
    assert "P0" in set(action_center["priority"])
    assert {"campaign_budget", "source_reliability", "data_quality"}.issubset(set(action_center["action_type"]))
    assert action_center.iloc[0]["priority"] == "P0"


def test_data_product_scorecard_rolls_up_operating_domains() -> None:
    source_health = pd.DataFrame(
        {
            "source_system": ["google_ads", "sales_conversions"],
            "accepted": [980, 900],
            "rows": [1000, 1000],
            "rejected": [20, 100],
            "quality_issue_count": [1, 4],
            "acceptance_rate": [0.98, 0.90],
            "rejection_rate": [0.02, 0.10],
            "source_health_status": ["healthy", "attention"],
            "latest_watermark": ["2026-05-15T00:00:00Z", None],
        }
    )
    data_quality = pd.DataFrame(
        {
            "source_system": ["google_ads", "sales_conversions"],
            "monitoring_status": ["healthy", "quality_warning"],
            "row_count": [1000, 1000],
            "rejected_count": [20, 100],
            "issue_count": [1, 4],
            "rejected_rate": [0.02, 0.10],
        }
    )
    action_center = pd.DataFrame(
        {
            "priority": ["P0", "P2"],
            "due_in_days": [1, 10],
            "owner_team": ["data_engineering", "growth_finance"],
        }
    )
    executive_scorecard = pd.DataFrame(
        {
            "executive_status": ["optimize"],
            "board_narrative": ["Platform is stable with known source risks."],
        }
    )
    journey_quality = pd.DataFrame(
        {
            "attribution_coverage": [0.92, 0.81],
            "orphan_conversion_rate": [0.01, 0.22],
            "journey_health_status": ["healthy", "stitching_risk"],
        }
    )
    attribution_reconciliation = pd.DataFrame(
        {"reconciliation_status": ["reconciled", "model_variance", "reconciled"]}
    )
    performance_forecast = pd.DataFrame({"forecast_roas": [2.2]})
    budget_scenarios = pd.DataFrame({"decision": ["approve", "hold"]})

    scorecard = _data_product_scorecard(
        source_health,
        data_quality,
        action_center,
        executive_scorecard,
        journey_quality,
        attribution_reconciliation,
        performance_forecast,
        budget_scenarios,
    )

    assert {
        "Source Reliability",
        "Incremental Readiness",
        "Data Quality",
        "Journey Stitching",
        "Attribution Reconciliation",
        "Action Management",
        "Executive Confidence",
        "Planning Readiness",
    }.issubset(set(scorecard["scorecard_domain"]))
    assert scorecard["score"].between(0, 100).all()
    assert "at_risk" in set(scorecard["score_status"])


def test_semantic_kpi_governance_contains_certified_bi_metrics() -> None:
    kpis = _semantic_kpi_governance()

    assert {"ROAS", "CAC", "Data Product Score", "Open Critical Actions"}.issubset(set(kpis["kpi_name"]))
    assert kpis["formula"].str.len().gt(0).all()
    assert kpis["source_marts"].str.contains("mart_").all()
    assert kpis["certified_status"].isin(["certified", "candidate"]).all()
