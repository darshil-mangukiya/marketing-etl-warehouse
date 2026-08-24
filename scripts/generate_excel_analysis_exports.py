from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "generated" / "excel_ready"
WORKBOOK_PATH = PROJECT_ROOT / "reports" / "generated" / "marketing_analysis_workbook.xlsx"


def _load_csv(name: str) -> pd.DataFrame:
    path = EXPORT_DIR / name
    if not path.exists() or path.stat().st_size <= 1:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numeric_numerator = pd.to_numeric(numerator, errors="coerce")
    numeric_denominator = pd.to_numeric(denominator, errors="coerce").mask(lambda series: series == 0)
    return numeric_numerator.div(numeric_denominator).fillna(0.0)


def build_channel_variance() -> pd.DataFrame:
    frame = _load_csv("demo_mart_channel_performance.csv")
    if frame.empty:
        return frame
    grouped = (
        frame.groupby(["reporting_month", "normalized_channel", "channel_name"], dropna=False)
        .agg(
            spend=("spend", "sum"),
            booked_revenue=("booked_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            leads=("leads", "sum"),
            closed_won_conversions=("closed_won_conversions", "sum"),
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
        )
        .reset_index()
    )
    total_spend = grouped["spend"].sum() or 1
    total_revenue = grouped["booked_revenue"].sum() or 1
    grouped["roas"] = _safe_divide(grouped["booked_revenue"], grouped["spend"])
    grouped["cac"] = _safe_divide(grouped["spend"], grouped["closed_won_conversions"])
    grouped["gross_margin_rate"] = _safe_divide(grouped["gross_margin"], grouped["booked_revenue"])
    grouped["spend_share"] = grouped["spend"] / total_spend
    grouped["revenue_share"] = grouped["booked_revenue"] / total_revenue
    grouped["efficiency_gap"] = grouped["revenue_share"] - grouped["spend_share"]
    return grouped.sort_values(["reporting_month", "efficiency_gap"], ascending=[True, False])


def build_target_vs_actual() -> pd.DataFrame:
    frame = _load_csv("demo_mart_target_vs_actual.csv")
    if frame.empty:
        return frame
    output = frame.copy()
    output["spend_variance"] = output["actual_spend"] - output["target_spend"]
    output["revenue_variance"] = output["actual_revenue"] - output["target_revenue"]
    output["lead_variance"] = output["actual_leads"] - output["target_leads"]
    output["spend_status"] = output["spend_attainment"].apply(lambda value: "over_target" if value > 1 else "under_target")
    output["revenue_status"] = output["revenue_attainment"].apply(lambda value: "met_or_above_target" if value >= 1 else "below_target")
    columns = [
        "target_month",
        "region",
        "channel",
        "budget_owner",
        "target_spend",
        "actual_spend",
        "spend_variance",
        "spend_attainment",
        "spend_status",
        "target_revenue",
        "actual_revenue",
        "revenue_variance",
        "revenue_attainment",
        "revenue_status",
        "target_leads",
        "actual_leads",
        "lead_variance",
        "lead_attainment",
    ]
    return output[[column for column in columns if column in output.columns]]


def build_funnel_conversion() -> pd.DataFrame:
    frame = _load_csv("demo_mart_funnel_performance.csv")
    if frame.empty:
        return frame
    output = frame.copy()
    output["lead_to_close_rate"] = _safe_divide(output["conversions"], output["total_leads"])
    output["funnel_review_flag"] = output.apply(
        lambda row: "review_sql_to_close" if row.get("sql_to_close_rate", 0) < 0.2 else "monitor",
        axis=1,
    )
    return output


def build_campaign_roi() -> pd.DataFrame:
    optimization = _load_csv("demo_mart_campaign_optimization.csv")
    campaign = _load_csv("demo_mart_campaign_performance.csv")
    if not optimization.empty:
        columns = [
            "optimization_rank",
            "campaign_id",
            "campaign_name",
            "normalized_channel",
            "spend",
            "conversions",
            "attributed_revenue",
            "attributed_roas",
            "cost_per_conversion",
            "spend_share",
            "revenue_share",
            "efficiency_gap",
            "opportunity_score",
            "waste_budget_flag",
            "recommended_action",
            "recommended_budget_shift_pct",
            "recommended_monthly_budget",
            "optimization_reason",
        ]
        return optimization[[column for column in columns if column in optimization.columns]].sort_values(
            ["waste_budget_flag", "opportunity_score"], ascending=[False, False]
        )
    if campaign.empty:
        return campaign
    return campaign.sort_values("attributed_roas", ascending=False)


def build_data_quality_summary() -> pd.DataFrame:
    quality = _load_csv("demo_mart_data_quality_monitoring.csv")
    source_health = _load_csv("demo_mart_source_health.csv")
    if quality.empty and source_health.empty:
        return pd.DataFrame()
    if quality.empty:
        return source_health
    summary = (
        quality.groupby("source_system", dropna=False)
        .agg(
            files_checked=("file", "count"),
            rows_checked=("row_count", "sum"),
            total_issues=("issue_count", "sum"),
            rejected_rows=("rejected_count", "sum"),
            failed_files=("status", lambda values: int((values == "failed").sum())),
        )
        .reset_index()
    )
    summary["rejection_rate"] = _safe_divide(summary["rejected_rows"], summary["rows_checked"])
    if not source_health.empty:
        health_columns = [
            "source_system",
            "files",
            "rows",
            "accepted",
            "rejected",
            "failed",
            "latest_watermark",
            "source_health_status",
        ]
        summary = summary.merge(
            source_health[[column for column in health_columns if column in source_health.columns]],
            on="source_system",
            how="left",
        )
    return summary


def build_readme(manifest: dict) -> str:
    rows = "\n".join(
        f"| `{item['file']}` | {item['rows']} | {item['source']} |" for item in manifest["outputs"]
    )
    return f"""# Excel-ready Analysis Outputs

Generated: `{manifest['generated_at']}`

These files are CSV exports designed for Excel pivot tables, variance analysis, target review, campaign ROI review, funnel conversion review, and data quality review. The data comes from generated marts in `data/exports/`.

| File | Rows | Source |
|---|---:|---|
{rows}

## Analysis Notes

- Use `channel_variance_analysis.csv` for channel-level spend, revenue, ROAS, CAC, margin, and share-of-total comparisons.
- Use `target_vs_actual_analysis.csv` for monthly target, actual, variance, and attainment review.
- Use `funnel_conversion_analysis.csv` for lead-to-MQL, MQL-to-SQL, SQL-to-close, and lead-to-close review.
- Use `campaign_roi_analysis.csv` for campaign profitability, waste flag, and optimization recommendation review.
- Use `data_quality_summary.csv` for source quality, rejection rate, failed files, and source-health review.

## Review Scope

- These outputs are generated by the local project pipeline.
- They support local validation and Excel-style analysis.
- They demonstrate reporting workflow design without exposing company performance data.
"""


def _write_workbook_if_available(outputs: dict[str, pd.DataFrame]) -> str | None:
    engine = None
    if importlib.util.find_spec("openpyxl"):
        engine = "openpyxl"
    elif importlib.util.find_spec("xlsxwriter"):
        engine = "xlsxwriter"
    if not engine:
        return None
    with pd.ExcelWriter(WORKBOOK_PATH, engine=engine) as writer:
        for sheet_name, frame in outputs.items():
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return str(WORKBOOK_PATH.relative_to(PROJECT_ROOT))


def generate_excel_analysis_exports() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "Channel Variance": build_channel_variance(),
        "Target vs Actual": build_target_vs_actual(),
        "Funnel Conversion": build_funnel_conversion(),
        "Campaign ROI": build_campaign_roi(),
        "Data Quality Summary": build_data_quality_summary(),
    }
    csv_manifest = []
    file_names = {
        "Channel Variance": "channel_variance_analysis.csv",
        "Target vs Actual": "target_vs_actual_analysis.csv",
        "Funnel Conversion": "funnel_conversion_analysis.csv",
        "Campaign ROI": "campaign_roi_analysis.csv",
        "Data Quality Summary": "data_quality_summary.csv",
    }
    source_names = {
        "Channel Variance": "data/exports/demo_mart_channel_performance.csv",
        "Target vs Actual": "data/exports/demo_mart_target_vs_actual.csv",
        "Funnel Conversion": "data/exports/demo_mart_funnel_performance.csv",
        "Campaign ROI": "data/exports/demo_mart_campaign_optimization.csv",
        "Data Quality Summary": "data/exports/demo_mart_data_quality_monitoring.csv and demo_mart_source_health.csv",
    }
    for name, frame in outputs.items():
        output_file = OUTPUT_DIR / file_names[name]
        frame.to_csv(output_file, index=False)
        csv_manifest.append(
            {
                "name": name,
                "file": str(output_file.relative_to(PROJECT_ROOT)),
                "rows": int(len(frame)),
                "source": source_names[name],
            }
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "csv_package",
        "outputs": csv_manifest,
        "workbook": _write_workbook_if_available(outputs),
    }
    readme = build_readme(manifest)
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    print(json.dumps(generate_excel_analysis_exports(), indent=2))


if __name__ == "__main__":
    main()
