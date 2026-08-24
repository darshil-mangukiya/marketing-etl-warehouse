import json
import zipfile
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_business_analysis_workbooks_are_valid_and_populated() -> None:
    expected = {
        "requirements_traceability_matrix.xlsx": {"Traceability", "Coverage Summary"},
        "data_source_assessment.xlsx": {"Source Assessment", "Status Legend"},
        "uat_test_plan.xlsx": {"Test Cases", "Test Plan", "Coverage Summary"},
    }
    for filename, required_names in expected.items():
        path = PROJECT_ROOT / "business_analysis" / filename
        assert path.stat().st_size > 5_000
        with zipfile.ZipFile(path) as archive:
            workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
            assert required_names <= {name for name in required_names if f'name="{name}"' in workbook_xml}
            assert "xl/styles.xml" in archive.namelist()


def test_powerbi_scenario_and_rls_assets_are_implementation_ready() -> None:
    manifest = json.loads(
        (PROJECT_ROOT / "semantic_layer/powerbi_tmdl/semantic_model_manifest.json").read_text(encoding="utf-8")
    )
    pages = yaml.safe_load(
        (PROJECT_ROOT / "semantic_layer/powerbi_tmdl/dashboard_pages.yml").read_text(encoding="utf-8")
    )
    roles = (PROJECT_ROOT / "semantic_layer/powerbi_tmdl/roles.tmdl").read_text(encoding="utf-8")

    assert manifest["table_count"] == 17
    assert manifest["measure_count"] == 59
    assert any(page["page"] == "Scenario Planning" for page in pages["dashboard_pages"])
    assert all(role in roles for role in ("Executive", "Channel Manager", "Regional Manager"))
    assert "dim_channel" in roles and "dim_region" in roles
    channels = pd.read_csv(PROJECT_ROOT / "dashboards/powerbi/data/dim_channel.csv")
    regions = pd.read_csv(PROJECT_ROOT / "dashboards/powerbi/data/dim_region.csv")
    assert set(channels.loc[channels["channel_group"].eq("Paid"), "channel_key"]) == {"paid_search", "paid_social"}
    assert regions.loc[regions["region"].eq("EMEA")].shape[0] == 1
    assert '[channel_group] = "Paid"' in roles and '[region] = "EMEA"' in roles


def test_decision_packet_has_required_governed_sections() -> None:
    packet = json.loads(
        (PROJECT_ROOT / "artifacts/decision_intelligence/latest_insight_packet.json").read_text(encoding="utf-8")
    )
    required = {
        "reporting_period", "kpi_snapshot", "material_changes", "anomalies", "variance_drivers",
        "top_campaigns", "funnel_issues", "target_gaps", "quality_warnings", "recommended_actions",
        "scenario_context", "evidence_references", "assumptions",
    }
    assert required <= packet.keys()
    assert packet["reconciliation"]["status"] == "PASS"


def test_airflow_orders_decision_intelligence_between_marts_and_reporting() -> None:
    dag = (PROJECT_ROOT / "airflow/dags/marketing_platform_daily.py").read_text(encoding="utf-8")
    assert "build_demo_marts\n            >> generate_decision_intelligence\n            >> generate_semantic_package" in dag
    assert "scripts/generate_decision_intelligence.py" in dag


def test_airflow_branch_join_runs_source_health_after_valid_path() -> None:
    dag = (PROJECT_ROOT / "airflow/dags/marketing_platform_daily.py").read_text(encoding="utf-8")
    assert 'task_id="refresh_source_health"' in dag
    assert "trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS" in dag
