from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.scenario_engine import ScenarioAdjustment, ScenarioInputs, run_standard_scenarios
from ingestion.prerequisites import ensure_ingestion_summary

OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "decision_intelligence"


def _read_json(relative_path: str) -> dict:
    return json.loads((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))


def _read_csv(relative_path: str) -> pd.DataFrame:
    path = PROJECT_ROOT / relative_path
    return pd.read_csv(path) if path.exists() and path.stat().st_size else pd.DataFrame()


def _read_first_csv(*relative_paths: str) -> pd.DataFrame:
    for relative_path in relative_paths:
        frame = _read_csv(relative_path)
        if not frame.empty:
            return frame
    return pd.DataFrame()


def _safe_total(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def _scenario_inputs(channel: pd.DataFrame) -> ScenarioInputs:
    spend = _safe_total(channel, "spend")
    clicks = _safe_total(channel, "clicks")
    conversions = _safe_total(channel, "closed_won_conversions")
    revenue = _safe_total(channel, "booked_revenue")
    grouped = channel.groupby("normalized_channel", dropna=False)["spend"].sum() if not channel.empty else pd.Series(dtype=float)
    allocations = (
        {str(name): float(value / spend) for name, value in grouped.items()}
        if spend
        else {"unallocated": 1.0}
    )
    return ScenarioInputs(
        total_budget=spend,
        channel_allocations=allocations,
        cpc=spend / clicks if clicks else 1.0,
        conversion_rate=min(1.0, conversions / clicks) if clicks else 0.0,
        aov=revenue / conversions if conversions else 0.0,
        target_roas=2.0,
        target_cac=250.0,
        growth_assumption=0.05,
        click_to_session_rate=0.9,
        customer_rate=1.0,
    )


def _warehouse_raw_counts() -> dict[str, int]:
    duckdb_manifest = PROJECT_ROOT / "data/logs/duckdb_raw_manifest.json"
    if duckdb_manifest.exists():
        warehouse = json.loads(duckdb_manifest.read_text(encoding="utf-8"))
        return {
            item["table"].split(".", 1)[1]: int(item["row_count"])
            for item in warehouse["raw_tables"]
            if item["table"].startswith("raw.")
        }

    from sqlalchemy import inspect, text
    from sqlalchemy.exc import SQLAlchemyError

    from ingestion.database import get_engine

    engine = get_engine()
    try:
        table_names = inspect(engine).get_table_names(schema="raw")
        quote = engine.dialect.identifier_preparer.quote
        with engine.connect() as connection:
            return {
                table_name: int(
                    connection.execute(text(f"select count(*) from raw.{quote(table_name)}")).scalar_one()
                )
                for table_name in table_names
            }
    except SQLAlchemyError:
        return {}


def build_reconciliation() -> dict[str, object]:
    source_manifest = _read_json("data_sources/generated/manifest.json")
    ingestion = ensure_ingestion_summary(PROJECT_ROOT)
    source_counts: dict[str, int] = {}
    for part in source_manifest["parts"]:
        source_counts[part["source_system"]] = source_counts.get(part["source_system"], 0) + int(part["row_count"])
    warehouse_counts = _warehouse_raw_counts()

    checks: list[dict[str, object]] = []
    for source, generated_rows in sorted(source_counts.items()):
        landed = ingestion["sources"].get(source, {})
        landed_rows = int(landed.get("rows", 0))
        accepted = int(landed.get("accepted", 0))
        rejected = int(landed.get("rejected", 0))
        warehouse_rows = warehouse_counts.get(source)
        checks.extend(
            [
                {
                    "check_id": f"SRC-LAND-{source}",
                    "stage": "source_to_landing",
                    "asset": source,
                    "metric": "row_count",
                    "source_value": generated_rows,
                    "target_value": landed_rows,
                    "variance": landed_rows - generated_rows,
                    "tolerance": 0,
                    "status": "PASS" if landed_rows == generated_rows else "FAIL",
                },
                {
                    "check_id": f"LAND-QUALITY-{source}",
                    "stage": "landing_quality",
                    "asset": source,
                    "metric": "accepted_plus_rejected",
                    "source_value": landed_rows,
                    "target_value": accepted + rejected,
                    "variance": accepted + rejected - landed_rows,
                    "tolerance": 0,
                    "status": "PASS" if accepted + rejected == landed_rows else "FAIL",
                },
                {
                    "check_id": f"LAND-WH-{source}",
                    "stage": "landing_to_warehouse",
                    "asset": source,
                    "metric": "raw_row_count",
                    "source_value": landed_rows,
                    "target_value": warehouse_rows,
                    "variance": None if warehouse_rows is None else warehouse_rows - landed_rows,
                    "tolerance": 0,
                    "status": "PASS" if warehouse_rows == landed_rows else "NOT_AVAILABLE" if warehouse_rows is None else "FAIL",
                },
            ]
        )

    pairs = [
        "mart_channel_performance",
        "mart_campaign_performance",
        "mart_funnel_performance",
        "mart_target_vs_actual",
        "mart_attribution_model_comparison",
        "mart_ga4_funnel",
        "mart_marketing_variance_drivers",
        "mart_campaign_action_center",
    ]
    metric_candidates = ["spend", "booked_revenue", "actual_revenue", "purchase_revenue", "conversions", "closed_won_conversions"]
    for table in pairs:
        mart = _read_csv(f"data/exports/demo_{table}.csv")
        bi = _read_csv(f"dashboards/powerbi/data/{table}.csv")
        source_available = not mart.empty
        checks.append(
            {
                "check_id": f"DBT-BI-{table}",
                "stage": "dbt_to_bi",
                "asset": table,
                "metric": "row_count",
                "source_value": len(mart),
                "target_value": len(bi),
                "variance": len(bi) - len(mart),
                "tolerance": 0,
                "status": "PASS" if len(mart) == len(bi) else "NOT_AVAILABLE" if not source_available else "FAIL",
            }
        )
        for metric in metric_candidates:
            if metric not in mart or metric not in bi:
                continue
            source_value = _safe_total(mart, metric)
            target_value = _safe_total(bi, metric)
            variance = target_value - source_value
            tolerance = max(0.01, abs(source_value) * 1e-9)
            checks.append(
                {
                    "check_id": f"DBT-BI-{table}-{metric}",
                    "stage": "dbt_to_bi",
                    "asset": table,
                    "metric": metric,
                    "source_value": source_value,
                    "target_value": target_value,
                    "variance": variance,
                    "tolerance": tolerance,
                    "status": "PASS" if abs(variance) <= tolerance else "FAIL",
                }
            )
    failed = sum(item["status"] == "FAIL" for item in checks)
    return {
        "generated_at": source_manifest["generated_at"],
        "classification": "LOCAL_PROJECT_RECONCILIATION",
        "check_count": len(checks),
        "passed_count": sum(item["status"] == "PASS" for item in checks),
        "failed_count": failed,
        "not_available_count": sum(item["status"] == "NOT_AVAILABLE" for item in checks),
        "overall_status": "PASS" if failed == 0 else "FAIL",
        "checks": checks,
    }


def build_insight_packet(scenarios: pd.DataFrame, reconciliation: dict[str, object]) -> dict[str, object]:
    channel = _read_csv("data/exports/demo_mart_channel_performance.csv")
    campaign = _read_csv("data/exports/demo_mart_campaign_performance.csv")
    variance = _read_first_csv(
        "data/exports/demo_mart_marketing_variance_drivers.csv",
        "dashboards/powerbi/data/mart_marketing_variance_drivers.csv",
    )
    anomalies = _read_csv("data/exports/demo_mart_marketing_anomalies.csv")
    funnel = _read_csv("data/exports/demo_mart_funnel_performance.csv")
    targets = _read_csv("data/exports/demo_mart_target_vs_actual.csv")
    quality = _read_csv("data/exports/demo_mart_data_quality_monitoring.csv")
    actions = _read_first_csv(
        "data/exports/demo_mart_campaign_action_center.csv",
        "data/exports/demo_mart_action_center.csv",
        "dashboards/powerbi/data/mart_campaign_action_center.csv",
    )
    reporting_period = str(pd.to_datetime(channel.get("reporting_month"), errors="coerce").max().date()) if not channel.empty else "not_available"

    top_campaigns = campaign.sort_values("attributed_revenue", ascending=False).head(5) if "attributed_revenue" in campaign else campaign.head(5)
    return {
        "reporting_period": reporting_period,
        "classification": "DETERMINISTIC_PROJECT_ANALYSIS",
        "kpi_snapshot": {
            "spend": _safe_total(channel, "spend"),
            "revenue": _safe_total(channel, "booked_revenue"),
            "closed_won_conversions": _safe_total(channel, "closed_won_conversions"),
            "roas": (_safe_total(channel, "booked_revenue") / _safe_total(channel, "spend")) if _safe_total(channel, "spend") else None,
            "cac": (_safe_total(channel, "spend") / _safe_total(channel, "closed_won_conversions")) if _safe_total(channel, "closed_won_conversions") else None,
            "source": "data/exports/demo_mart_channel_performance.csv",
        },
        "material_changes": variance.head(10).to_dict(orient="records"),
        "anomalies": anomalies.head(10).to_dict(orient="records"),
        "variance_drivers": variance.head(10).to_dict(orient="records"),
        "top_campaigns": top_campaigns.to_dict(orient="records"),
        "funnel_issues": funnel.sort_values("sql_to_close_rate", ascending=True).head(5).to_dict(orient="records") if "sql_to_close_rate" in funnel else funnel.head(5).to_dict(orient="records"),
        "target_gaps": targets.sort_values("revenue_variance", ascending=True).head(5).to_dict(orient="records") if "revenue_variance" in targets else targets.head(5).to_dict(orient="records"),
        "quality_warnings": quality[quality.get("monitoring_status", pd.Series(index=quality.index, dtype=str)).ne("healthy")].head(10).to_dict(orient="records"),
        "recommended_actions": actions.head(10).to_dict(orient="records"),
        "scenario_context": scenarios.groupby("scenario_name", dropna=False).agg(
            projected_spend=("channel_budget", "sum"),
            projected_revenue=("projected_revenue", "sum"),
            projected_customers=("projected_customers", "sum"),
        ).reset_index().to_dict(orient="records"),
        "reconciliation": {
            "status": reconciliation["overall_status"],
            "passed": reconciliation["passed_count"],
            "failed": reconciliation["failed_count"],
            "evidence": "artifacts/decision_intelligence/source_to_target_reconciliation.json",
        },
        "evidence_references": [
            "data/exports/demo_mart_channel_performance.csv",
            "data/exports/demo_mart_marketing_anomalies.csv",
            "data/exports/demo_mart_marketing_variance_drivers.csv",
            "data/exports/demo_mart_campaign_action_center.csv",
            "dashboards/powerbi/data/mart_budget_scenarios.csv",
        ],
        "assumptions": [
            "Campaign, CRM, sales, target, and local GA4-style datasets are generated by the project pipeline.",
            "Scenario outputs are simulations and require human review.",
            "Diagnostic drivers and anomalies do not establish causality.",
        ],
    }


def generate() -> dict[str, str | int]:
    channel = _read_csv("data/exports/demo_mart_channel_performance.csv")
    scenario_rows = run_standard_scenarios(
        _scenario_inputs(channel),
        user_defined=ScenarioAdjustment(budget_multiplier=1.1, conversion_multiplier=1.05),
    )
    scenarios = pd.DataFrame(scenario_rows)
    demo_scenario_path = PROJECT_ROOT / "data" / "exports" / "demo_mart_budget_scenarios.csv"
    demo_scenario_path.parent.mkdir(parents=True, exist_ok=True)
    scenarios.to_csv(demo_scenario_path, index=False)
    scenario_path = PROJECT_ROOT / "dashboards" / "powerbi" / "data" / "mart_budget_scenarios.csv"
    scenario_path.parent.mkdir(parents=True, exist_ok=True)
    scenarios.to_csv(scenario_path, index=False)

    reconciliation = build_reconciliation()
    packet = build_insight_packet(scenarios, reconciliation)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reconciliation_path = OUTPUT_DIR / "source_to_target_reconciliation.json"
    packet_path = OUTPUT_DIR / "latest_insight_packet.json"
    reconciliation_path.write_text(json.dumps(reconciliation, indent=2, default=str) + "\n", encoding="utf-8")
    packet_path.write_text(json.dumps(packet, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "scenario_rows": len(scenarios),
        "reconciliation_checks": reconciliation["check_count"],
        "reconciliation_status": reconciliation["overall_status"],
        "scenario_output": scenario_path.relative_to(PROJECT_ROOT).as_posix(),
        "packet_output": packet_path.relative_to(PROJECT_ROOT).as_posix(),
    }


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
