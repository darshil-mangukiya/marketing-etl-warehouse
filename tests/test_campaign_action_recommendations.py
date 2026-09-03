from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_campaign_action_recommendations_export_exists_with_required_fields() -> None:
    path = PROJECT_ROOT / "data" / "exports" / "analyst_outputs" / "campaign_action_recommendations.csv"
    assert path.exists()

    frame = pd.read_csv(path)
    required = {
        "campaign_id",
        "campaign_name",
        "channel",
        "platform",
        "region",
        "spend",
        "revenue",
        "roas",
        "campaign_roi_pct",
        "cac",
        "conversion_rate",
        "lead_to_customer_rate",
        "budget_pacing_pct",
        "target_attainment_pct",
        "attribution_coverage_pct",
        "data_quality_flag",
        "recommended_action",
        "action_priority",
        "action_reason",
    }
    assert required.issubset(frame.columns)
    assert len(frame) > 0

    allowed_actions = {
        "Scale",
        "Pause",
        "Monitor",
        "Reallocate Budget",
        "Improve Funnel Quality",
        "Investigate Attribution Gap",
        "Fix Data Quality Issue",
    }
    assert set(frame["recommended_action"].dropna()).issubset(allowed_actions)
    assert set(frame["action_priority"].dropna()).issubset({"P0", "P1", "P2", "P3"})


def test_campaign_action_recommendation_report_documents_logic() -> None:
    report = PROJECT_ROOT / "reports" / "campaign_action_recommendations.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    for phrase in [
        "Business Purpose",
        "Scoring Logic",
        "Scale",
        "Pause",
        "Reallocate Budget",
        "Investigate Attribution Gap",
        "Fix Data Quality Issue",
        "Review Scope",
    ]:
        assert phrase in text
