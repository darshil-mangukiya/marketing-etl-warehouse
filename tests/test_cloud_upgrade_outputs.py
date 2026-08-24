from __future__ import annotations

import json
from pathlib import Path

import duckdb

from scripts.export_cloud_upgrade_outputs import export_upgrade_outputs


def test_upgrade_export_writes_powerbi_tables_and_executive_sections(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "test.duckdb"
    connection = duckdb.connect(str(database))
    connection.execute("create schema mart")
    connection.execute("create table mart.mart_ga4_funnel as select 1 as sessions, 0.0 as purchase_revenue")
    connection.execute("create table mart.mart_marketing_variance_drivers as select 'HIGH' as severity")
    connection.execute("create table mart.mart_campaign_action_center as select 'REDUCE' as recommended_action")
    connection.execute("create table mart.mart_data_quality_monitoring as select 'warning' as monitoring_status")
    connection.close()

    powerbi = tmp_path / "powerbi"
    reports = tmp_path / "reports"
    monkeypatch.setattr("scripts.export_cloud_upgrade_outputs.POWERBI_DIR", powerbi)
    monkeypatch.setattr("scripts.export_cloud_upgrade_outputs.REPORT_DIR", reports)
    manifest = export_upgrade_outputs(database)
    assert manifest["execution_state"] == "simulated_local"
    assert (powerbi / "mart_ga4_funnel.csv").exists()
    brief = (reports / "executive_marketing_diagnostic_brief.md").read_text(encoding="utf-8")
    for section in ["What Changed", "Why It Changed", "Largest Drivers", "Campaigns Requiring Attention", "Recommended Actions", "Data Quality Risks", "Metrics to Monitor"]:
        assert f"## {section}" in brief
    assert json.loads((reports / "cloud_upgrade_output_manifest.json").read_text())["tables"]["mart_ga4_funnel"] == 1
