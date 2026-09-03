from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HANDOFF_ROOT = PROJECT_ROOT / "data" / "exports" / "powerbi_handoff"


def test_powerbi_handoff_required_docs_exist() -> None:
    required = [
        "README.md",
        "relationships.md",
        "dax_measures.md",
        "powerbi_build_steps.md",
        "page_specs.md",
        "measure_table_setup.md",
        "power_query_steps.md",
        "screenshot_checklist.md",
    ]
    for item in required:
        assert (HANDOFF_ROOT / item).exists(), item


def test_powerbi_handoff_csv_tables_exist() -> None:
    required = [
        "dim_date.csv",
        "dim_campaign.csv",
        "dim_channel.csv",
        "dim_region.csv",
        "dim_device.csv",
        "dim_customer_segment.csv",
        "fact_campaign_performance.csv",
        "fact_ad_spend.csv",
        "fact_leads.csv",
        "fact_conversions.csv",
        "fact_revenue_attribution.csv",
        "fact_budget_targets.csv",
        "mart_campaign_action_recommendations.csv",
    ]
    for item in required:
        assert (HANDOFF_ROOT / item).exists(), item


def test_powerbi_handoff_scope_is_honest() -> None:
    pbix_files = sorted(PROJECT_ROOT.glob("**/*.pbix"))
    assert pbix_files == [PROJECT_ROOT / "dashboards" / "powerbi" / "p2_marketing_performance_dashboard.pbix"]
    readme = (HANDOFF_ROOT / "README.md").read_text(encoding="utf-8").lower()
    checklist = (HANDOFF_ROOT / "screenshot_checklist.md").read_text(encoding="utf-8").lower()
    assert "completed editable dashboard" in readme
    assert "refresh screenshot evidence" in checklist
    assert "published power bi dashboard" not in readme
