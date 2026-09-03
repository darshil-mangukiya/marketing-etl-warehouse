from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "warehouse" / "campaign_roi.duckdb"
POWERBI_DIR = PROJECT_ROOT / "dashboards" / "powerbi" / "data"
REPORT_DIR = PROJECT_ROOT / "reports" / "generated"

TABLES = [
    "mart_ga4_funnel",
    "mart_marketing_variance_drivers",
    "mart_campaign_action_center",
    "mart_data_quality_monitoring",
]


def export_upgrade_outputs(database_path: Path = DATABASE_PATH) -> dict:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("DuckDB is required to export local upgrade marts.") from exc
    if not database_path.exists():
        raise FileNotFoundError(f"DuckDB warehouse not found: {database_path}. Run the raw load and dbt build first.")

    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        for table in TABLES:
            frame = connection.execute(f"select * from mart.{table}").fetchdf()
            frame.to_csv(POWERBI_DIR / f"{table}.csv", index=False)
            frames[table] = frame
    finally:
        connection.close()

    action = frames["mart_campaign_action_center"]
    variance = frames["mart_marketing_variance_drivers"]
    quality = frames["mart_data_quality_monitoring"]
    action_counts = action.get("recommended_action", pd.Series(dtype=str)).value_counts().to_dict()
    severity_counts = variance.get("severity", pd.Series(dtype=str)).value_counts().to_dict()
    quality_risks = quality.loc[quality.get("monitoring_status", pd.Series(index=quality.index, dtype=str)) != "healthy"]
    generated_at = datetime.now(timezone.utc).isoformat()
    brief = f"""# Executive Marketing Diagnostic Brief

Generated: {generated_at}

All values use generated project data. Diagnostic drivers describe contributing movements and do not establish causality.

## What Changed

Variance-driver rows by severity: {json.dumps(severity_counts, sort_keys=True)}.

## Why It Changed

The governed mart compares current and prior spend, impressions, clicks, CTR, CPC, conversions, revenue, AOV, CAC and ROAS. Review `mart_marketing_variance_drivers.csv` for primary and secondary diagnostic labels.

## Largest Drivers

High/medium drivers: {int(variance.get('severity', pd.Series(dtype=str)).isin(['HIGH', 'MEDIUM']).sum())}.

## Campaigns Requiring Attention

Action distribution: {json.dumps(action_counts, sort_keys=True)}.

## Recommended Actions

Use the transparent action, reason, supporting metric and metric-to-monitor fields. A data-quality hold overrides performance action.

## Data Quality Risks

Non-healthy monitoring rows: {len(quality_risks)}. Investigate these before distributing results.

## Metrics to Monitor

ROAS, CAC, conversion rate, revenue, spend variance, source freshness, rejected rows and last successful watermark.
"""
    report_path = REPORT_DIR / "executive_marketing_diagnostic_brief.md"
    report_path.write_text(brief, encoding="utf-8")
    manifest = {
        "generated_at": generated_at,
        "database_path": _display_path(database_path),
        "tables": {table: len(frame) for table, frame in frames.items()},
        "report": _display_path(report_path),
        "execution_state": "simulated_local",
    }
    (REPORT_DIR / "cloud_upgrade_output_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    print(json.dumps(export_upgrade_outputs(), indent=2))
