from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_executive_insights_export_and_markdown_exist() -> None:
    csv_path = PROJECT_ROOT / "data" / "exports" / "analyst_outputs" / "executive_insights.csv"
    report_path = PROJECT_ROOT / "reports" / "executive_insights_summary.md"
    assert csv_path.exists()
    assert report_path.exists()

    frame = pd.read_csv(csv_path)
    required = {
        "insight_id",
        "insight_category",
        "insight_title",
        "insight_detail",
        "evidence_metric",
        "recommended_action",
        "priority",
    }
    assert required.issubset(frame.columns)
    assert len(frame) >= 5


def test_executive_insights_cover_required_categories() -> None:
    frame = pd.read_csv(PROJECT_ROOT / "data" / "exports" / "analyst_outputs" / "executive_insights.csv")
    categories = set(frame["insight_category"].str.lower())
    expected_any = {
        "channel efficiency",
        "campaign roi",
        "funnel drop-off",
        "target attainment",
        "attribution differences",
        "customer value",
        "source/data quality",
        "recommended next actions",
    }
    assert len(categories & expected_any) >= 6

    report = (PROJECT_ROOT / "reports" / "executive_insights_summary.md").read_text(encoding="utf-8")
    for phrase in [
        "Executive Summary",
        "Top 5 Insights",
        "Risks To Review",
        "Opportunities To Scale",
        "Data-Quality Caveats",
        "Recommended 30/60/90-Day Actions",
    ]:
        assert phrase in report
