from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.attribution_models import (
    normalize_weights,
    position_based_weight,
    time_decay_raw_score,
    u_shaped_weight,
)
from analytics.anomaly_detection import detect_marketing_anomalies
from ingestion.config import PlatformConfig
from ingestion.file_io import read_frame


DATA_QUALITY_COLUMNS = [
    "source_system",
    "file",
    "report",
    "row_count",
    "status",
    "issue_count",
    "rejected_count",
    "rejected_rate",
    "monitoring_status",
]

SOURCE_HEALTH_COLUMNS = [
    "source_system",
    "files",
    "rows",
    "accepted",
    "rejected",
    "failed",
    "skipped",
    "latest_watermark",
    "watermark_captured_at",
    "quality_issue_count",
    "failed_quality_files",
    "rejection_rate",
    "acceptance_rate",
    "source_health_status",
]


def read_csv_optional(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size <= 1:
        return pd.DataFrame(columns=columns or [])
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame(columns=columns or [])


def source_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("source_system="):
            return part.split("=", 1)[1]
    return "unknown"


def read_raw_source(config: PlatformConfig, source_system: str) -> pd.DataFrame:
    root = config.data_lake_root / "raw" / f"source_system={source_system}"
    batch_roots = sorted(root.glob("load_date=*/batch_id=*"), key=lambda path: path.name)
    search_root = batch_roots[-1] if batch_roots else root
    frames = []
    for pattern in ("*.csv", "*.jsonl", "*.parquet"):
        for file_path in sorted(search_root.rglob(pattern)):
            frames.append(read_frame(file_path))
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def normalize_channel(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    normalized = str(value).strip().lower().replace(" ", "_")
    if normalized in {"google_ads", "paid_search", "sem", "google"}:
        return "paid_search"
    if normalized in {"facebook_ads", "facebook", "tiktok_ads", "tik_tok", "paid_social"}:
        return "paid_social"
    if normalized in {"organic_search", "organic"}:
        return "organic"
    if normalized in {"email", "lifecycle"}:
        return "email"
    if normalized in {"direct", "referral"}:
        return normalized
    return "unknown"


def build_demo_marts() -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    paid = []
    for source_system, default_channel in [
        ("google_ads", "paid_search"),
        ("facebook_ads", "paid_social"),
        ("tiktok_ads", "paid_social"),
    ]:
        frame = read_raw_source(config, source_system)
        if frame.empty:
            continue
        frame["source_system"] = source_system
        frame["normalized_channel"] = default_channel
        if "event_date" in frame.columns:
            frame["event_date"] = pd.to_datetime(frame["event_date"], errors="coerce")
        if "video_views" in frame.columns and "impressions" not in frame.columns:
            frame["impressions"] = frame["video_views"]
        frame["spend"] = pd.to_numeric(frame.get("spend", 0), errors="coerce").fillna(0)
        frame["clicks"] = pd.to_numeric(frame.get("clicks", 0), errors="coerce").fillna(0)
        frame["impressions"] = pd.to_numeric(frame.get("impressions", 0), errors="coerce").fillna(0)
        frame["conversions"] = pd.to_numeric(frame.get("conversions", 0), errors="coerce").fillna(0)
        paid.append(frame)
    paid_media = pd.concat(paid, ignore_index=True, sort=False) if paid else pd.DataFrame()

    leads = read_raw_source(config, "crm_leads")
    sales = read_raw_source(config, "sales_conversions")
    targets = read_raw_source(config, "marketing_targets")
    sessions = read_raw_source(config, "website_analytics")
    quality_path = config.quality_report_dir / "latest_quality_summary.csv"
    quality = read_csv_optional(quality_path)

    if not paid_media.empty:
        paid_media["reporting_month"] = paid_media["event_date"].dt.to_period("M").dt.to_timestamp()
        channel = (
            paid_media.groupby(["reporting_month", "normalized_channel"], dropna=False)
            .agg(
                spend=("spend", "sum"),
                impressions=("impressions", "sum"),
                clicks=("clicks", "sum"),
                platform_conversions=("conversions", "sum"),
            )
            .reset_index()
        )
    else:
        channel = pd.DataFrame(columns=["reporting_month", "normalized_channel", "spend", "impressions", "clicks"])

    if not leads.empty:
        leads["created_date"] = pd.to_datetime(leads.get("created_at"), errors="coerce")
        leads["reporting_month"] = leads["created_date"].dt.to_period("M").dt.to_timestamp()
        leads["normalized_channel"] = leads.get("lead_source", "unknown").map(normalize_channel)
        lead_agg = (
            leads.groupby(["reporting_month", "normalized_channel"], dropna=False)
            .agg(
                leads=("lead_id", "count"),
                qualified_leads=(
                    "qualification_stage",
                    lambda value: value.isin(["marketing_qualified", "sales_accepted", "sales_qualified"]).sum(),
                ),
            )
            .reset_index()
        )
    else:
        lead_agg = pd.DataFrame(columns=["reporting_month", "normalized_channel", "leads", "qualified_leads"])

    if not sales.empty:
        sales["conversion_date"] = pd.to_datetime(sales.get("conversion_date"), errors="coerce")
        sales["reporting_month"] = sales["conversion_date"].dt.to_period("M").dt.to_timestamp()
        sales["deal_value"] = pd.to_numeric(sales.get("deal_value", 0), errors="coerce").fillna(0)
        sales["gross_margin"] = pd.to_numeric(sales.get("gross_margin", 0), errors="coerce").fillna(0)
        sales["normalized_channel"] = "unknown"
        sales_agg = (
            sales.groupby(["reporting_month", "normalized_channel"], dropna=False)
            .agg(
                closed_won_conversions=("conversion_id", "count"),
                booked_revenue=("deal_value", "sum"),
                gross_margin=("gross_margin", "sum"),
            )
            .reset_index()
        )
    else:
        sales_agg = pd.DataFrame(
            columns=["reporting_month", "normalized_channel", "closed_won_conversions", "booked_revenue", "gross_margin"]
        )

    channel_perf = channel.merge(lead_agg, how="outer", on=["reporting_month", "normalized_channel"]).merge(
        sales_agg, how="outer", on=["reporting_month", "normalized_channel"]
    )
    channel_perf = channel_perf.fillna(
        {
            "spend": 0,
            "impressions": 0,
            "clicks": 0,
            "platform_conversions": 0,
            "leads": 0,
            "qualified_leads": 0,
            "closed_won_conversions": 0,
            "booked_revenue": 0,
            "gross_margin": 0,
        }
    )
    channel_perf["channel_name"] = channel_perf["normalized_channel"].map(
        {
            "paid_search": "Paid Search",
            "paid_social": "Paid Social",
            "email": "Email",
            "organic": "Organic Search",
            "direct": "Direct",
            "referral": "Referral",
            "unknown": "Unknown",
        }
    )
    channel_perf["ctr"] = safe_divide(channel_perf["clicks"], channel_perf["impressions"])
    channel_perf["cpc"] = safe_divide(channel_perf["spend"], channel_perf["clicks"])
    channel_perf["cac"] = safe_divide(channel_perf["spend"], channel_perf["closed_won_conversions"])
    channel_perf["roas"] = safe_divide(channel_perf["booked_revenue"], channel_perf["spend"])
    channel_perf["mer"] = safe_divide(channel_perf["gross_margin"], channel_perf["spend"])

    campaign_perf = _campaign_performance(paid_media)
    funnel_perf = _funnel_performance(leads, sales)
    target_vs_actual = _target_vs_actual(targets, channel_perf)
    attribution_summary = _attribution_summary(sales)
    attribution_comparison = _attribution_comparison(attribution_summary)
    customer_value = _customer_value(sales)
    budget_efficiency = _budget_efficiency(channel_perf)
    data_quality = _data_quality_monitoring(quality)
    if data_quality.empty:
        data_quality = read_csv_optional(
            config.export_dir / "demo_mart_data_quality_monitoring.csv",
            DATA_QUALITY_COLUMNS,
        )
    device_perf = _device_performance(sessions)
    executive_scorecard = _executive_scorecard(channel_perf, budget_efficiency, data_quality)
    budget_pacing = _budget_pacing(target_vs_actual)
    conversion_lag = _conversion_lag(leads, sales)
    customer_segment_mix = _customer_segment_mix(customer_value)
    journey_quality = _journey_quality(leads, sales, sessions)
    source_health = _source_health(config, data_quality)
    if source_health.empty:
        source_health = read_csv_optional(
            config.export_dir / "demo_mart_source_health.csv",
            SOURCE_HEALTH_COLUMNS,
        )
    campaign_optimization = _campaign_optimization(campaign_perf)
    regional_performance = _regional_performance(paid_media, leads, sales, sessions)
    product_performance = _product_performance(leads, sales)
    marketing_anomalies = _marketing_anomalies(channel_perf, source_health)
    attribution_reconciliation = _attribution_reconciliation(channel_perf, attribution_summary)
    performance_forecast = _performance_forecast(channel_perf)
    budget_scenarios = _budget_scenarios(channel_perf, campaign_optimization)
    customer_cohort_retention = _customer_cohort_retention(leads, sales)
    action_center = _action_center(
        campaign_optimization,
        budget_pacing,
        marketing_anomalies,
        source_health,
        data_quality,
        budget_scenarios,
        performance_forecast,
    )
    executive_briefing = _executive_briefing(
        executive_scorecard,
        campaign_optimization,
        regional_performance,
        product_performance,
        marketing_anomalies,
        budget_pacing,
        source_health,
    )
    data_product_scorecard = _data_product_scorecard(
        source_health,
        data_quality,
        action_center,
        executive_scorecard,
        journey_quality,
        attribution_reconciliation,
        performance_forecast,
        budget_scenarios,
    )
    semantic_kpi_governance = _semantic_kpi_governance()

    outputs = {
        "mart_executive_scorecard": executive_scorecard,
        "mart_executive_briefing": executive_briefing,
        "mart_channel_performance": channel_perf,
        "mart_campaign_performance": campaign_perf,
        "mart_campaign_optimization": campaign_optimization,
        "mart_funnel_performance": funnel_perf,
        "mart_target_vs_actual": target_vs_actual,
        "mart_budget_pacing": budget_pacing,
        "mart_attribution_summary": attribution_summary,
        "mart_attribution_model_comparison": attribution_comparison,
        "mart_customer_value": customer_value,
        "mart_customer_segment_mix": customer_segment_mix,
        "mart_budget_efficiency": budget_efficiency,
        "mart_conversion_lag": conversion_lag,
        "mart_journey_quality": journey_quality,
        "mart_regional_performance": regional_performance,
        "mart_product_performance": product_performance,
        "mart_marketing_anomalies": marketing_anomalies,
        "mart_attribution_reconciliation": attribution_reconciliation,
        "mart_performance_forecast": performance_forecast,
        "mart_budget_scenarios": budget_scenarios,
        "mart_customer_cohort_retention": customer_cohort_retention,
        "mart_action_center": action_center,
        "mart_data_product_scorecard": data_product_scorecard,
        "mart_semantic_kpi_governance": semantic_kpi_governance,
        "mart_data_quality_monitoring": data_quality,
        "mart_device_performance": device_perf,
        "mart_source_health": source_health,
    }
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "pandas_demo_marts",
        "tables": [],
    }
    for table_name, frame in outputs.items():
        output_path = config.export_dir / f"demo_{table_name}.csv"
        frame.to_csv(output_path, index=False)
        manifest["tables"].append(
            {"table": table_name, "row_count": len(frame), "file": str(output_path.relative_to(config.project_root))}
        )
    manifest_path = config.export_dir / "demo_mart_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numerator_numeric = pd.to_numeric(numerator, errors="coerce").fillna(0).astype(float)
    denominator_numeric = pd.to_numeric(denominator, errors="coerce").astype(float)
    denominator_numeric = denominator_numeric.where(denominator_numeric != 0)
    return numerator_numeric.div(denominator_numeric).fillna(0)


def _campaign_performance(paid_media: pd.DataFrame) -> pd.DataFrame:
    if paid_media.empty:
        return pd.DataFrame()
    frame = paid_media.copy()
    frame["campaign_name"] = frame.get("campaign_name", "Unknown").fillna("Unknown").astype(str).str.strip()
    grouped = (
        frame.groupby(["campaign_id", "campaign_name", "normalized_channel"], dropna=False)
        .agg(spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"), conversions=("conversions", "sum"))
        .reset_index()
    )
    grouped["attributed_revenue"] = grouped["conversions"] * 275.0
    grouped["attributed_roas"] = safe_divide(grouped["attributed_revenue"], grouped["spend"])
    grouped["waste_budget_flag"] = (grouped["spend"] > grouped["spend"].quantile(0.75)) & (grouped["attributed_roas"] < 1.0)
    return grouped.sort_values("spend", ascending=False).head(250)


def _funnel_performance(leads: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    if leads.empty:
        return pd.DataFrame()
    frame = leads.copy()
    frame["created_date"] = pd.to_datetime(frame.get("created_at"), errors="coerce")
    frame["reporting_month"] = frame["created_date"].dt.to_period("M").dt.to_timestamp()
    frame["normalized_channel"] = frame.get("lead_source", "unknown").map(normalize_channel)
    grouped = (
        frame.groupby(["reporting_month", "normalized_channel"], dropna=False)
        .agg(
            total_leads=("lead_id", "count"),
            mqls=("qualification_stage", lambda value: value.eq("marketing_qualified").sum()),
            sales_accepted_leads=("qualification_stage", lambda value: value.eq("sales_accepted").sum()),
            sales_qualified_leads=("qualification_stage", lambda value: value.eq("sales_qualified").sum()),
        )
        .reset_index()
    )
    conversions = 0 if sales.empty else len(sales)
    grouped["conversions"] = (grouped["sales_qualified_leads"] / grouped["sales_qualified_leads"].sum() * conversions).fillna(0)
    grouped["lead_to_mql_rate"] = safe_divide(grouped["mqls"], grouped["total_leads"])
    grouped["mql_to_sql_rate"] = safe_divide(grouped["sales_qualified_leads"], grouped["mqls"])
    grouped["sql_to_close_rate"] = safe_divide(grouped["conversions"], grouped["sales_qualified_leads"])
    return grouped


def _target_vs_actual(targets: pd.DataFrame, channel_perf: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame()
    frame = targets.copy()
    frame["target_month"] = pd.to_datetime(frame.get("target_month").astype(str) + "-01", errors="coerce")
    actuals = (
        channel_perf.groupby(["reporting_month", "normalized_channel"], dropna=False)
        .agg(actual_spend=("spend", "sum"), actual_revenue=("booked_revenue", "sum"), actual_leads=("leads", "sum"))
        .reset_index()
    )
    merged = frame.merge(
        actuals,
        how="left",
        left_on=["target_month", "channel"],
        right_on=["reporting_month", "normalized_channel"],
    ).fillna({"actual_spend": 0, "actual_revenue": 0, "actual_leads": 0})
    merged["spend_attainment"] = safe_divide(merged["actual_spend"], merged["target_spend"])
    merged["revenue_attainment"] = safe_divide(merged["actual_revenue"], merged["target_revenue"])
    merged["lead_attainment"] = safe_divide(merged["actual_leads"], merged["target_leads"])
    return merged


def _attribution_summary(sales: pd.DataFrame) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame()
    frame = sales.copy()
    frame["conversion_date"] = pd.to_datetime(frame.get("conversion_date"), errors="coerce")
    frame["reporting_month"] = frame["conversion_date"].dt.to_period("M").dt.to_timestamp()
    frame["deal_value"] = pd.to_numeric(frame.get("deal_value", 0), errors="coerce").fillna(0)
    rows = []
    model_multipliers = {
        "first_touch": 0.94,
        "last_touch": 1.08,
        "linear": 1.0,
        "u_shaped": 1.04,
        "time_decay": 1.12,
        "position_based": 1.02,
    }
    frame["simulated_touchpoint_count"] = (frame.index % 5) + 1
    frame["simulated_days_to_conversion"] = (frame.index % 28).astype(float)
    for model, multiplier in model_multipliers.items():
        working = frame.copy()
        if model == "u_shaped":
            working["model_weight"] = [
                u_shaped_weight(int(count), 1, 1 if count == 1 else int(count))
                for count in working["simulated_touchpoint_count"]
            ]
        elif model == "position_based":
            working["model_weight"] = [
                position_based_weight(int(count), 1, 1 if count == 1 else int(count))
                for count in working["simulated_touchpoint_count"]
            ]
        elif model == "time_decay":
            raw = [time_decay_raw_score(days) for days in working["simulated_days_to_conversion"]]
            working["model_weight"] = normalize_weights(raw)
            working["model_weight"] = working["model_weight"] * len(working)
        else:
            working["model_weight"] = 1.0
        working["attributed_revenue"] = working["deal_value"] * working["model_weight"] * multiplier
        grouped = working.groupby("reporting_month", dropna=False).agg(
            attributed_conversions=("conversion_id", "count"),
            weighted_conversions=("model_weight", "sum"),
            attributed_revenue=("attributed_revenue", "sum"),
        )
        grouped["attribution_model"] = model
        rows.append(grouped.reset_index())
    return pd.concat(rows, ignore_index=True)


def _attribution_comparison(attribution_summary: pd.DataFrame) -> pd.DataFrame:
    if attribution_summary.empty:
        return pd.DataFrame()
    pivot = attribution_summary.pivot_table(
        index="reporting_month",
        columns="attribution_model",
        values="attributed_revenue",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    pivot.columns.name = None
    for column in ["first_touch", "last_touch", "linear", "u_shaped", "time_decay", "position_based"]:
        if column not in pivot.columns:
            pivot[column] = 0.0
    pivot["last_vs_first_revenue_delta"] = pivot["last_touch"] - pivot["first_touch"]
    pivot["time_decay_vs_linear_revenue_delta"] = pivot["time_decay"] - pivot["linear"]
    pivot["u_shaped_vs_linear_revenue_delta"] = pivot["u_shaped"] - pivot["linear"]
    return pivot.rename(
        columns={
            "first_touch": "first_touch_revenue",
            "last_touch": "last_touch_revenue",
            "linear": "linear_revenue",
            "u_shaped": "u_shaped_revenue",
            "time_decay": "time_decay_revenue",
            "position_based": "position_based_revenue",
        }
    )


def _customer_value(sales: pd.DataFrame) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame()
    frame = sales.copy()
    frame["deal_value"] = pd.to_numeric(frame.get("deal_value", 0), errors="coerce").fillna(0)
    frame["gross_margin"] = pd.to_numeric(frame.get("gross_margin", 0), errors="coerce").fillna(0)
    grouped = (
        frame.groupby("customer_id", dropna=False)
        .agg(purchase_count=("conversion_id", "count"), lifetime_revenue=("deal_value", "sum"), lifetime_margin=("gross_margin", "sum"))
        .reset_index()
    )
    grouped["customer_segment"] = pd.cut(
        grouped["lifetime_revenue"],
        bins=[-1, 0, 8000, 25000, float("inf")],
        labels=["pre_conversion", "smb_value", "mid_market_value", "enterprise_value"],
    ).astype(str)
    return grouped


def _budget_efficiency(channel_perf: pd.DataFrame) -> pd.DataFrame:
    frame = channel_perf.copy()
    frame["contribution_after_marketing"] = frame["gross_margin"] - frame["spend"]
    frame["budget_recommendation"] = "watch"
    frame.loc[(frame["roas"] >= 4) & (frame["cac"] <= 500), "budget_recommendation"] = "scale"
    frame.loc[(frame["roas"] >= 2) & (frame["roas"] < 4), "budget_recommendation"] = "maintain"
    frame.loc[frame["roas"] < 1, "budget_recommendation"] = "cut_or_fix"
    frame.loc[frame["spend"] == 0, "budget_recommendation"] = "no_spend"
    return frame


def _data_quality_monitoring(quality: pd.DataFrame) -> pd.DataFrame:
    if quality.empty:
        return pd.DataFrame()
    frame = quality.copy()
    frame["rejected_rate"] = safe_divide(frame["rejected_count"], frame["row_count"])
    frame["monitoring_status"] = "healthy"
    frame.loc[frame["rejected_rate"] > 0.02, "monitoring_status"] = "quality_warning"
    frame.loc[frame["status"].eq("failed") & (frame["rejected_rate"] > 0.05), "monitoring_status"] = "quality_failure"
    return frame


def _device_performance(sessions: pd.DataFrame) -> pd.DataFrame:
    if sessions.empty:
        return pd.DataFrame()
    frame = sessions.copy()
    frame["event_date"] = pd.to_datetime(frame.get("event_date"), errors="coerce")
    frame["reporting_month"] = frame["event_date"].dt.to_period("M").dt.to_timestamp()
    frame["page_views"] = pd.to_numeric(frame.get("page_views", 0), errors="coerce").fillna(0)
    frame["bounce_flag"] = pd.to_numeric(frame.get("bounce_flag", 0), errors="coerce").fillna(0)
    grouped = (
        frame.groupby(["reporting_month", "device"], dropna=False)
        .agg(sessions=("session_id", "count"), page_views=("page_views", "sum"), bounce_rate=("bounce_flag", "mean"))
        .reset_index()
    )
    return grouped


def _executive_scorecard(
    channel_perf: pd.DataFrame,
    budget_efficiency: pd.DataFrame,
    data_quality: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "snapshot_month",
        "spend",
        "booked_revenue",
        "gross_margin",
        "leads",
        "closed_won_conversions",
        "roas",
        "cac",
        "lead_to_close_rate",
        "gross_margin_rate",
        "spend_mom_pct",
        "revenue_mom_pct",
        "gross_margin_mom_pct",
        "quality_warning_count",
        "quality_failure_count",
        "scale_recommendation_count",
        "fix_recommendation_count",
        "executive_status",
        "board_narrative",
    ]
    if channel_perf.empty:
        return pd.DataFrame(columns=columns)

    frame = channel_perf.copy()
    frame["reporting_month"] = pd.to_datetime(frame["reporting_month"], errors="coerce")
    for column in [
        "spend",
        "booked_revenue",
        "gross_margin",
        "leads",
        "closed_won_conversions",
    ]:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)

    monthly = (
        frame.groupby("reporting_month", dropna=False)
        .agg(
            spend=("spend", "sum"),
            booked_revenue=("booked_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            leads=("leads", "sum"),
            closed_won_conversions=("closed_won_conversions", "sum"),
        )
        .reset_index()
        .sort_values("reporting_month")
    )
    monthly["roas"] = safe_divide(monthly["booked_revenue"], monthly["spend"])
    monthly["cac"] = safe_divide(monthly["spend"], monthly["closed_won_conversions"])
    monthly["lead_to_close_rate"] = safe_divide(monthly["closed_won_conversions"], monthly["leads"])
    monthly["gross_margin_rate"] = safe_divide(monthly["gross_margin"], monthly["booked_revenue"])
    current = monthly.iloc[-1]
    previous = monthly.iloc[-2] if len(monthly) > 1 else None

    def mom(column: str) -> float:
        if previous is None or float(previous[column]) == 0:
            return 0.0
        return (float(current[column]) - float(previous[column])) / float(previous[column])

    if data_quality.empty:
        quality_warning_count = 0
        quality_failure_count = 0
    else:
        quality_warning_count = int(data_quality["monitoring_status"].eq("quality_warning").sum())
        quality_failure_count = int(data_quality["monitoring_status"].eq("quality_failure").sum())

    latest_month = current["reporting_month"]
    if budget_efficiency.empty:
        scale_recommendation_count = 0
        fix_recommendation_count = 0
    else:
        budget_frame = budget_efficiency.copy()
        budget_frame["reporting_month"] = pd.to_datetime(budget_frame["reporting_month"], errors="coerce")
        latest_budget = budget_frame[budget_frame["reporting_month"].eq(latest_month)]
        scale_recommendation_count = int(latest_budget["budget_recommendation"].eq("scale").sum())
        fix_recommendation_count = int(latest_budget["budget_recommendation"].eq("cut_or_fix").sum())

    roas_value = float(current["roas"])
    margin_value = float(current["gross_margin"])
    spend_value = float(current["spend"])
    revenue_mom = mom("booked_revenue")
    if quality_failure_count:
        executive_status = "data_risk"
        board_narrative = "Quality failures require review before leadership decisions."
    elif roas_value >= 3 and revenue_mom >= 0:
        executive_status = "scale"
        board_narrative = "Revenue efficiency is strong enough to expand selected channels."
    elif roas_value < 1 or margin_value < spend_value:
        executive_status = "profitability_watch"
        board_narrative = "Marketing is not yet covering spend with margin."
    else:
        executive_status = "optimize"
        board_narrative = "Platform is stable; optimize weak campaigns and attribution gaps."

    row = {
        "snapshot_month": current["reporting_month"],
        "spend": current["spend"],
        "booked_revenue": current["booked_revenue"],
        "gross_margin": current["gross_margin"],
        "leads": current["leads"],
        "closed_won_conversions": current["closed_won_conversions"],
        "roas": current["roas"],
        "cac": current["cac"],
        "lead_to_close_rate": current["lead_to_close_rate"],
        "gross_margin_rate": current["gross_margin_rate"],
        "spend_mom_pct": mom("spend"),
        "revenue_mom_pct": revenue_mom,
        "gross_margin_mom_pct": mom("gross_margin"),
        "quality_warning_count": quality_warning_count,
        "quality_failure_count": quality_failure_count,
        "scale_recommendation_count": scale_recommendation_count,
        "fix_recommendation_count": fix_recommendation_count,
        "executive_status": executive_status,
        "board_narrative": board_narrative,
    }
    return pd.DataFrame([row], columns=columns)


def _budget_pacing(target_vs_actual: pd.DataFrame) -> pd.DataFrame:
    if target_vs_actual.empty:
        return pd.DataFrame()
    frame = target_vs_actual.copy()
    frame["target_month"] = pd.to_datetime(frame["target_month"], errors="coerce")
    for column in [
        "target_spend",
        "target_revenue",
        "target_leads",
        "actual_spend",
        "actual_revenue",
        "actual_leads",
    ]:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)

    grouped = (
        frame.groupby(["target_month", "channel", "budget_owner"], dropna=False)
        .agg(
            target_spend=("target_spend", "sum"),
            target_revenue=("target_revenue", "sum"),
            target_leads=("target_leads", "sum"),
            actual_spend=("actual_spend", "max"),
            actual_revenue=("actual_revenue", "max"),
            actual_leads=("actual_leads", "max"),
        )
        .reset_index()
    )
    grouped["remaining_budget"] = grouped["target_spend"] - grouped["actual_spend"]
    grouped["revenue_gap"] = grouped["target_revenue"] - grouped["actual_revenue"]
    grouped["lead_gap"] = grouped["target_leads"] - grouped["actual_leads"]
    grouped["spend_attainment"] = safe_divide(grouped["actual_spend"], grouped["target_spend"])
    grouped["revenue_attainment"] = safe_divide(grouped["actual_revenue"], grouped["target_revenue"])
    grouped["lead_attainment"] = safe_divide(grouped["actual_leads"], grouped["target_leads"])
    grouped["efficiency_score"] = grouped["revenue_attainment"] - (grouped["spend_attainment"] - 1).clip(lower=0)
    grouped["pacing_status"] = "watch"
    grouped.loc[
        (grouped["revenue_attainment"] >= 1) & (grouped["spend_attainment"] <= 1.05),
        "pacing_status",
    ] = "overachieving_efficient"
    grouped.loc[
        (grouped["revenue_attainment"] >= 0.9) & grouped["pacing_status"].eq("watch"),
        "pacing_status",
    ] = "on_track"
    grouped.loc[
        (grouped["spend_attainment"] > 1.05) & (grouped["revenue_attainment"] < 0.9),
        "pacing_status",
    ] = "overspending_underperforming"
    grouped.loc[grouped["revenue_attainment"] < 0.7, "pacing_status"] = "under_pacing"
    return grouped.sort_values(["target_month", "channel", "budget_owner"])


def _conversion_lag(leads: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame()
    sales_frame = sales.copy()
    sales_frame["conversion_date"] = pd.to_datetime(sales_frame.get("conversion_date"), errors="coerce")
    sales_frame["created_at"] = pd.to_datetime(sales_frame.get("created_at"), errors="coerce")
    sales_frame["deal_value"] = pd.to_numeric(sales_frame.get("deal_value", 0), errors="coerce").fillna(0)
    sales_frame["gross_margin"] = pd.to_numeric(sales_frame.get("gross_margin", 0), errors="coerce").fillna(0)

    if leads.empty:
        joined = sales_frame.assign(
            lead_created_at=pd.NaT,
            lead_source="unknown",
            qualification_stage="unknown",
            region="unknown",
        )
    else:
        lead_columns = ["lead_id", "created_at", "lead_source", "qualification_stage", "region"]
        lead_lookup = leads[lead_columns].drop_duplicates("lead_id").rename(columns={"created_at": "lead_created_at"})
        lead_lookup["lead_created_at"] = pd.to_datetime(lead_lookup["lead_created_at"], errors="coerce")
        joined = sales_frame.merge(lead_lookup, how="left", on="lead_id")

    joined["origin_date"] = joined["lead_created_at"].combine_first(joined["created_at"])
    joined["conversion_lag_days"] = (
        joined["conversion_date"].sub(joined["origin_date"]).dt.days.clip(lower=0).fillna(0)
    )
    joined["normalized_channel"] = joined["lead_source"].map(normalize_channel).fillna("unknown")
    joined["product"] = joined.get("product", "unknown").fillna("unknown")
    joined["conversion_lag_bucket"] = pd.cut(
        joined["conversion_lag_days"],
        bins=[-1, 7, 14, 30, 60, 120, float("inf")],
        labels=["0-7 days", "8-14 days", "15-30 days", "31-60 days", "61-120 days", "120+ days"],
    ).astype(str)
    grouped = (
        joined.groupby(["normalized_channel", "product", "conversion_lag_bucket"], dropna=False)
        .agg(
            conversions=("conversion_id", "count"),
            booked_revenue=("deal_value", "sum"),
            gross_margin=("gross_margin", "sum"),
            avg_conversion_lag_days=("conversion_lag_days", "mean"),
        )
        .reset_index()
    )
    grouped["revenue_per_conversion"] = safe_divide(grouped["booked_revenue"], grouped["conversions"])
    return grouped.sort_values(["normalized_channel", "product", "avg_conversion_lag_days"])


def _customer_segment_mix(customer_value: pd.DataFrame) -> pd.DataFrame:
    if customer_value.empty:
        return pd.DataFrame()
    frame = customer_value.copy()
    for column in ["purchase_count", "lifetime_revenue", "lifetime_margin"]:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)
    grouped = (
        frame.groupby("customer_segment", dropna=False)
        .agg(
            customers=("customer_id", "count"),
            purchases=("purchase_count", "sum"),
            lifetime_revenue=("lifetime_revenue", "sum"),
            lifetime_margin=("lifetime_margin", "sum"),
        )
        .reset_index()
    )
    grouped["avg_revenue_per_customer"] = safe_divide(grouped["lifetime_revenue"], grouped["customers"])
    grouped["avg_purchases_per_customer"] = safe_divide(grouped["purchases"], grouped["customers"])
    grouped["margin_rate"] = safe_divide(grouped["lifetime_margin"], grouped["lifetime_revenue"])
    grouped["segment_priority"] = "nurture"
    grouped.loc[grouped["margin_rate"] >= 0.45, "segment_priority"] = "expand"
    grouped.loc[grouped["lifetime_revenue"].eq(0), "segment_priority"] = "activate"
    return grouped.sort_values("lifetime_revenue", ascending=False)


def _journey_quality(leads: pd.DataFrame, sales: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    channels = pd.DataFrame({"normalized_channel": ["paid_search", "paid_social", "email", "organic", "direct", "referral", "unknown"]})
    if not leads.empty:
        lead_frame = leads.copy()
        lead_frame["normalized_channel"] = lead_frame.get("lead_source", "unknown").map(normalize_channel)
        lead_frame["lead_score"] = pd.to_numeric(lead_frame.get("lead_score", 0), errors="coerce").fillna(0)
        lead_frame["missing_attribution"] = lead_frame.get("attribution_id").isna() | lead_frame.get("attribution_id").astype(str).str.strip().eq("")
        lead_agg = (
            lead_frame.groupby("normalized_channel", dropna=False)
            .agg(
                leads=("lead_id", "count"),
                leads_missing_attribution=("missing_attribution", "sum"),
                avg_lead_score=("lead_score", "mean"),
            )
            .reset_index()
        )
    else:
        lead_agg = pd.DataFrame(columns=["normalized_channel", "leads", "leads_missing_attribution", "avg_lead_score"])

    if not sessions.empty:
        session_frame = sessions.copy()
        session_frame["normalized_channel"] = session_frame.get("traffic_source", "unknown").map(normalize_channel)
        session_frame["missing_campaign_id"] = (
            session_frame.get("utm_campaign_id").isna()
            | session_frame.get("utm_campaign_id").astype(str).str.strip().eq("")
        )
        session_frame["bounce_flag"] = pd.to_numeric(session_frame.get("bounce_flag", 0), errors="coerce").fillna(0)
        session_agg = (
            session_frame.groupby("normalized_channel", dropna=False)
            .agg(
                sessions=("session_id", "count"),
                sessions_missing_campaign=("missing_campaign_id", "sum"),
                bounce_rate=("bounce_flag", "mean"),
            )
            .reset_index()
        )
    else:
        session_agg = pd.DataFrame(columns=["normalized_channel", "sessions", "sessions_missing_campaign", "bounce_rate"])

    if not sales.empty:
        sales_frame = sales.copy()
        if "normalized_channel" in sales_frame.columns:
            sales_frame = sales_frame.drop(columns=["normalized_channel"])
        lead_lookup = pd.DataFrame(columns=["lead_id", "normalized_channel"])
        if not leads.empty:
            lead_lookup = leads[["lead_id", "lead_source"]].drop_duplicates("lead_id")
            lead_lookup["normalized_channel"] = lead_lookup["lead_source"].map(normalize_channel)
            lead_lookup = lead_lookup[["lead_id", "normalized_channel"]]
        sales_frame = sales_frame.merge(lead_lookup, how="left", on="lead_id")
        sales_frame["normalized_channel"] = sales_frame["normalized_channel"].fillna("unknown")
        sales_frame["deal_value"] = pd.to_numeric(sales_frame.get("deal_value", 0), errors="coerce").fillna(0)
        known_leads = set(lead_lookup["lead_id"].dropna())
        sales_frame["orphan_conversion"] = sales_frame["lead_id"].eq("UNKNOWN") | ~sales_frame["lead_id"].isin(known_leads)
        sales_frame["missing_attribution"] = (
            sales_frame.get("attribution_id").isna()
            | sales_frame.get("attribution_id").astype(str).str.strip().eq("")
        )
        sales_agg = (
            sales_frame.groupby("normalized_channel", dropna=False)
            .agg(
                conversions=("conversion_id", "count"),
                orphan_conversions=("orphan_conversion", "sum"),
                conversions_missing_attribution=("missing_attribution", "sum"),
                booked_revenue=("deal_value", "sum"),
            )
            .reset_index()
        )
    else:
        sales_agg = pd.DataFrame(
            columns=[
                "normalized_channel",
                "conversions",
                "orphan_conversions",
                "conversions_missing_attribution",
                "booked_revenue",
            ]
        )

    joined = channels.merge(session_agg, how="outer", on="normalized_channel").merge(
        lead_agg, how="outer", on="normalized_channel"
    ).merge(sales_agg, how="outer", on="normalized_channel")
    joined = joined.fillna(
        {
            "sessions": 0,
            "sessions_missing_campaign": 0,
            "bounce_rate": 0,
            "leads": 0,
            "leads_missing_attribution": 0,
            "avg_lead_score": 0,
            "conversions": 0,
            "orphan_conversions": 0,
            "conversions_missing_attribution": 0,
            "booked_revenue": 0,
        }
    )
    joined["session_to_lead_rate"] = safe_divide(joined["leads"], joined["sessions"])
    joined["lead_to_conversion_rate"] = safe_divide(joined["conversions"], joined["leads"])
    joined["orphan_conversion_rate"] = safe_divide(joined["orphan_conversions"], joined["conversions"])
    missing_attribution = joined["leads_missing_attribution"] + joined["conversions_missing_attribution"]
    measurable_records = joined["leads"] + joined["conversions"]
    joined["attribution_coverage"] = 1 - safe_divide(missing_attribution, measurable_records)
    joined["journey_health_status"] = "healthy"
    joined.loc[
        (joined["orphan_conversion_rate"] > 0.2) | (joined["attribution_coverage"] < 0.85),
        "journey_health_status",
    ] = "stitching_risk"
    joined.loc[
        (joined["journey_health_status"].eq("healthy"))
        & ((joined["bounce_rate"] > 0.65) | (joined["lead_to_conversion_rate"] < 0.02)),
        "journey_health_status",
    ] = "journey_watch"
    return joined.sort_values("booked_revenue", ascending=False)


def _source_health(config: PlatformConfig, data_quality: pd.DataFrame) -> pd.DataFrame:
    summary_path = config.log_dir / "latest_ingestion_summary.json"
    watermark_path = config.watermark_path
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    watermarks = json.loads(watermark_path.read_text(encoding="utf-8")) if watermark_path.exists() else {}
    sources = summary.get("sources", {})
    rows = []
    for source_system, payload in sources.items():
        rows.append(
            {
                "source_system": source_system,
                "files": payload.get("files", 0),
                "rows": payload.get("rows", 0),
                "accepted": payload.get("accepted", 0),
                "rejected": payload.get("rejected", 0),
                "failed": payload.get("failed", 0),
                "skipped": payload.get("skipped", 0),
                "latest_watermark": watermarks.get(source_system, {}).get("max_updated_at"),
                "watermark_captured_at": watermarks.get(source_system, {}).get("updated_at"),
            }
        )
    source_health = pd.DataFrame(rows)
    if source_health.empty:
        return pd.DataFrame()
    if data_quality.empty:
        quality_agg = pd.DataFrame(columns=["source_system", "quality_issue_count", "failed_quality_files"])
    else:
        quality_agg = (
            data_quality.groupby("source_system", dropna=False)
            .agg(
                quality_issue_count=("issue_count", "sum"),
                failed_quality_files=("monitoring_status", lambda value: value.isin(["quality_warning", "quality_failure"]).sum()),
            )
            .reset_index()
        )
    source_health = source_health.merge(quality_agg, how="left", on="source_system").fillna(
        {"quality_issue_count": 0, "failed_quality_files": 0}
    )
    source_health["rejection_rate"] = safe_divide(source_health["rejected"], source_health["rows"])
    source_health["acceptance_rate"] = safe_divide(source_health["accepted"], source_health["rows"])
    source_health["source_health_status"] = "healthy"
    source_health.loc[
        (source_health["failed"] > 0) | (source_health["failed_quality_files"] > 0),
        "source_health_status",
    ] = "attention"
    source_health.loc[
        (source_health["source_health_status"].eq("healthy")) & (source_health["rejection_rate"] > 0.02),
        "source_health_status",
    ] = "quality_watch"
    return source_health.sort_values(["source_health_status", "source_system"])


def _standardize_region(value: object) -> str:
    if pd.isna(value):
        return "Unknown"
    normalized = str(value).strip().upper()
    if normalized in {"", "NAN", "NONE", "UNKNOWN"}:
        return "Unknown"
    mapping = {
        "US": "NA",
        "USA": "NA",
        "CA": "NA",
        "CANADA": "NA",
        "MX": "LATAM",
        "BR": "LATAM",
        "AR": "LATAM",
        "CL": "LATAM",
        "GB": "EMEA",
        "UK": "EMEA",
        "DE": "EMEA",
        "FR": "EMEA",
        "NL": "EMEA",
        "ES": "EMEA",
        "IT": "EMEA",
        "IN": "APAC",
        "AU": "APAC",
        "JP": "APAC",
        "SG": "APAC",
    }
    return mapping.get(normalized, normalized)


def _campaign_optimization(campaign_perf: pd.DataFrame) -> pd.DataFrame:
    if campaign_perf.empty:
        return pd.DataFrame()
    frame = campaign_perf.copy()
    for column in ["spend", "impressions", "clicks", "conversions", "attributed_revenue", "attributed_roas"]:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)
    frame["cost_per_conversion"] = safe_divide(frame["spend"], frame["conversions"])
    frame["spend_share"] = safe_divide(frame["spend"], pd.Series([frame["spend"].sum()] * len(frame), index=frame.index))
    frame["revenue_share"] = safe_divide(
        frame["attributed_revenue"],
        pd.Series([frame["attributed_revenue"].sum()] * len(frame), index=frame.index),
    )
    frame["efficiency_gap"] = frame["revenue_share"] - frame["spend_share"]
    frame["opportunity_score"] = frame["attributed_roas"] * np.log1p(frame["conversions"]) + (frame["efficiency_gap"] * 10)
    conversion_median = frame["conversions"].median()
    high_spend_threshold = frame["spend"].quantile(0.75)
    frame["recommended_action"] = "monitor"
    frame.loc[(frame["attributed_roas"] >= 4) & (frame["conversions"] >= conversion_median), "recommended_action"] = "scale"
    frame.loc[(frame["attributed_roas"].between(2, 4, inclusive="left")), "recommended_action"] = "maintain"
    frame.loc[(frame["spend"] >= high_spend_threshold) & (frame["attributed_roas"] < 1), "recommended_action"] = "reduce"
    frame.loc[(frame["conversions"] == 0) & (frame["spend"] > 0), "recommended_action"] = "pause_or_rebuild"
    frame["recommended_budget_shift_pct"] = 0.0
    frame.loc[frame["recommended_action"].eq("scale"), "recommended_budget_shift_pct"] = 0.20
    frame.loc[frame["recommended_action"].eq("maintain"), "recommended_budget_shift_pct"] = 0.00
    frame.loc[frame["recommended_action"].eq("reduce"), "recommended_budget_shift_pct"] = -0.25
    frame.loc[frame["recommended_action"].eq("pause_or_rebuild"), "recommended_budget_shift_pct"] = -0.50
    frame["recommended_monthly_budget"] = frame["spend"] * (1 + frame["recommended_budget_shift_pct"])
    frame["optimization_reason"] = "Balanced spend and conversion performance."
    frame.loc[
        frame["recommended_action"].eq("scale"),
        "optimization_reason",
    ] = "High ROAS with enough conversion volume to justify budget expansion."
    frame.loc[
        frame["recommended_action"].eq("reduce"),
        "optimization_reason",
    ] = "High spend is not producing enough attributed revenue."
    frame.loc[
        frame["recommended_action"].eq("pause_or_rebuild"),
        "optimization_reason",
    ] = "Spend has produced no measurable conversions."
    frame["optimization_rank"] = frame["opportunity_score"].rank(ascending=False, method="dense").astype(int)
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
    return frame.sort_values(["recommended_action", "optimization_rank"])[columns]


def _regional_performance(
    paid_media: pd.DataFrame,
    leads: pd.DataFrame,
    sales: pd.DataFrame,
    sessions: pd.DataFrame,
) -> pd.DataFrame:
    key_columns = ["region", "normalized_channel"]
    if not paid_media.empty:
        paid = paid_media.copy()
        paid["region"] = paid.get("region").combine_first(paid.get("country")) if "region" in paid.columns else paid.get("country")
        paid["region"] = paid["region"].map(_standardize_region)
        paid_agg = (
            paid.groupby(key_columns, dropna=False)
            .agg(
                spend=("spend", "sum"),
                impressions=("impressions", "sum"),
                clicks=("clicks", "sum"),
                platform_conversions=("conversions", "sum"),
            )
            .reset_index()
        )
    else:
        paid_agg = pd.DataFrame(columns=key_columns + ["spend", "impressions", "clicks", "platform_conversions"])

    if not sessions.empty:
        session_frame = sessions.copy()
        session_frame["region"] = session_frame.get("country", "Unknown").map(_standardize_region)
        session_frame["normalized_channel"] = session_frame.get("traffic_source", "unknown").map(normalize_channel)
        session_frame["page_views"] = pd.to_numeric(session_frame.get("page_views", 0), errors="coerce").fillna(0)
        session_frame["bounce_flag"] = pd.to_numeric(session_frame.get("bounce_flag", 0), errors="coerce").fillna(0)
        session_agg = (
            session_frame.groupby(key_columns, dropna=False)
            .agg(
                sessions=("session_id", "count"),
                page_views=("page_views", "sum"),
                bounce_rate=("bounce_flag", "mean"),
            )
            .reset_index()
        )
    else:
        session_agg = pd.DataFrame(columns=key_columns + ["sessions", "page_views", "bounce_rate"])

    if not leads.empty:
        lead_frame = leads.copy()
        lead_frame["region"] = lead_frame.get("region", "Unknown").map(_standardize_region)
        lead_frame["normalized_channel"] = lead_frame.get("lead_source", "unknown").map(normalize_channel)
        lead_agg = (
            lead_frame.groupby(key_columns, dropna=False)
            .agg(
                leads=("lead_id", "count"),
                qualified_leads=(
                    "qualification_stage",
                    lambda value: value.isin(["marketing_qualified", "sales_accepted", "sales_qualified"]).sum(),
                ),
            )
            .reset_index()
        )
    else:
        lead_agg = pd.DataFrame(columns=key_columns + ["leads", "qualified_leads"])

    if not sales.empty:
        sales_frame = sales.copy()
        if not leads.empty:
            lead_lookup = leads[["lead_id", "lead_source", "region"]].drop_duplicates("lead_id")
            sales_frame = sales_frame.merge(lead_lookup, how="left", on="lead_id", suffixes=("", "_lead"))
            sales_frame["normalized_channel"] = sales_frame["lead_source"].map(normalize_channel).fillna("unknown")
            sales_frame["region"] = sales_frame["region"].map(_standardize_region)
        else:
            sales_frame["normalized_channel"] = "unknown"
            sales_frame["region"] = "Unknown"
        sales_frame["deal_value"] = pd.to_numeric(sales_frame.get("deal_value", 0), errors="coerce").fillna(0)
        sales_frame["gross_margin"] = pd.to_numeric(sales_frame.get("gross_margin", 0), errors="coerce").fillna(0)
        sales_agg = (
            sales_frame.groupby(key_columns, dropna=False)
            .agg(
                closed_won_conversions=("conversion_id", "count"),
                booked_revenue=("deal_value", "sum"),
                gross_margin=("gross_margin", "sum"),
            )
            .reset_index()
        )
    else:
        sales_agg = pd.DataFrame(columns=key_columns + ["closed_won_conversions", "booked_revenue", "gross_margin"])

    regional = (
        paid_agg.merge(session_agg, how="outer", on=key_columns)
        .merge(lead_agg, how="outer", on=key_columns)
        .merge(sales_agg, how="outer", on=key_columns)
    )
    for column in [
        "spend",
        "impressions",
        "clicks",
        "platform_conversions",
        "sessions",
        "page_views",
        "bounce_rate",
        "leads",
        "qualified_leads",
        "closed_won_conversions",
        "booked_revenue",
        "gross_margin",
    ]:
        regional[column] = pd.to_numeric(regional.get(column, 0), errors="coerce").fillna(0)
    regional["roas"] = safe_divide(regional["booked_revenue"], regional["spend"])
    regional["cac"] = safe_divide(regional["spend"], regional["closed_won_conversions"])
    regional["session_to_lead_rate"] = safe_divide(regional["leads"], regional["sessions"])
    regional["lead_to_close_rate"] = safe_divide(regional["closed_won_conversions"], regional["leads"])
    regional["margin_rate"] = safe_divide(regional["gross_margin"], regional["booked_revenue"])
    regional["market_status"] = "watch"
    regional.loc[(regional["roas"] >= 3) & (regional["lead_to_close_rate"] >= 0.05), "market_status"] = "scale_market"
    regional.loc[(regional["spend"] > 0) & (regional["roas"] < 1), "market_status"] = "profitability_risk"
    regional.loc[(regional["sessions"] > 0) & (regional["session_to_lead_rate"] < 0.05), "market_status"] = "conversion_risk"
    return regional.sort_values(["region", "booked_revenue"], ascending=[True, False])


def _product_performance(leads: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame()
    frame = sales.copy()
    if not leads.empty:
        lookup = leads[["lead_id", "lead_source", "region"]].drop_duplicates("lead_id")
        frame = frame.merge(lookup, how="left", on="lead_id")
        frame["normalized_channel"] = frame["lead_source"].map(normalize_channel).fillna("unknown")
        frame["region"] = frame["region"].map(_standardize_region)
    else:
        frame["normalized_channel"] = "unknown"
        frame["region"] = "Unknown"
    frame["product"] = frame.get("product", "Unknown").fillna("Unknown")
    frame["deal_value"] = pd.to_numeric(frame.get("deal_value", 0), errors="coerce").fillna(0)
    frame["gross_margin"] = pd.to_numeric(frame.get("gross_margin", 0), errors="coerce").fillna(0)
    grouped = (
        frame.groupby(["product", "normalized_channel", "region"], dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            conversions=("conversion_id", "count"),
            booked_revenue=("deal_value", "sum"),
            gross_margin=("gross_margin", "sum"),
        )
        .reset_index()
    )
    grouped["avg_deal_value"] = safe_divide(grouped["booked_revenue"], grouped["conversions"])
    grouped["margin_rate"] = safe_divide(grouped["gross_margin"], grouped["booked_revenue"])
    grouped["revenue_rank"] = grouped["booked_revenue"].rank(ascending=False, method="dense").astype(int)
    grouped["product_priority"] = "maintain"
    grouped.loc[(grouped["revenue_rank"] <= 5) & (grouped["margin_rate"] >= 0.45), "product_priority"] = "feature_in_campaigns"
    grouped.loc[grouped["margin_rate"] < 0.25, "product_priority"] = "pricing_or_margin_review"
    return grouped.sort_values(["booked_revenue", "gross_margin"], ascending=False)


def _marketing_anomalies(channel_perf: pd.DataFrame, source_health: pd.DataFrame) -> pd.DataFrame:
    if channel_perf.empty:
        return pd.DataFrame()
    frame = channel_perf.copy()
    frame["reporting_month"] = pd.to_datetime(frame["reporting_month"], errors="coerce")
    numeric_columns = [
        "spend",
        "booked_revenue",
        "gross_margin",
        "impressions",
        "clicks",
        "leads",
        "closed_won_conversions",
        "roas",
        "cac",
    ]
    for column in numeric_columns:
        source = frame[column] if column in frame else pd.Series(0.0, index=frame.index)
        frame[column] = pd.to_numeric(source, errors="coerce").fillna(0)
    frame["ctr"] = safe_divide(frame["clicks"], frame["impressions"])
    frame["cpc"] = safe_divide(frame["spend"], frame["clicks"])
    frame["conversion_rate"] = safe_divide(frame["closed_won_conversions"], frame["clicks"])
    frame["aov"] = safe_divide(frame["booked_revenue"], frame["closed_won_conversions"])
    anomalies = detect_marketing_anomalies(frame)
    if not source_health.empty:
        health_rows = source_health[source_health["source_health_status"].ne("healthy")]
        source_rows = []
        for _, row in health_rows.iterrows():
            source_system = row["source_system"]
            rejected = float(row.get("rejected", 0))
            rejection_rate = float(row.get("rejection_rate", 0))
            source_rows.append(
                {
                    "reporting_month": pd.NaT,
                    "normalized_channel": "source_health",
                    "entity_type": "source_system",
                    "entity_value": source_system,
                    "metric_name": f"{source_system}_source_health",
                    "current_value": rejected,
                    "baseline_value": 0.0,
                    "prior_value": 0.0,
                    "deviation_value": rejected,
                    "pct_change": rejection_rate,
                    "robust_z_score": 0.0,
                    "z_score": 0.0,
                    "severity": "high" if row.get("source_health_status") == "attention" else "medium",
                    "detection_method": "source_quality_status",
                    "evidence": f"status={row.get('source_health_status')}; rejected={rejected:.0f}; rate={rejection_rate:.1%}",
                    "investigation_hint": f"{source_system} has source-health status {row.get('source_health_status')}.",
                }
            )
        if source_rows:
            anomalies = pd.concat([anomalies, pd.DataFrame(source_rows)], ignore_index=True)
    if anomalies.empty:
        return anomalies
    return anomalies.sort_values(["severity", "reporting_month"], ascending=[True, False])


def _attribution_reconciliation(channel_perf: pd.DataFrame, attribution_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if not channel_perf.empty:
        frame = channel_perf.copy()
        frame["reporting_month"] = pd.to_datetime(frame["reporting_month"], errors="coerce")
        for column in ["platform_conversions", "closed_won_conversions", "booked_revenue"]:
            frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)
        grouped = (
            frame.groupby(["reporting_month", "normalized_channel"], dropna=False)
            .agg(
                platform_conversions=("platform_conversions", "sum"),
                closed_won_conversions=("closed_won_conversions", "sum"),
                booked_revenue=("booked_revenue", "sum"),
            )
            .reset_index()
        )
        for _, row in grouped.iterrows():
            variance = row["platform_conversions"] - row["closed_won_conversions"]
            variance_rate = 0 if row["closed_won_conversions"] == 0 else variance / row["closed_won_conversions"]
            status = "reconciled" if abs(variance_rate) <= 0.10 else "explain_variance"
            rows.append(
                {
                    "reporting_month": row["reporting_month"],
                    "normalized_channel": row["normalized_channel"],
                    "comparison_type": "platform_vs_sales_conversions",
                    "source_metric": "platform_conversions",
                    "warehouse_metric": "closed_won_conversions",
                    "source_value": row["platform_conversions"],
                    "warehouse_value": row["closed_won_conversions"],
                    "variance_value": variance,
                    "variance_rate": variance_rate,
                    "reconciliation_status": status,
                }
            )
    if not channel_perf.empty and not attribution_summary.empty:
        actual = (
            channel_perf.groupby("reporting_month", dropna=False)
            .agg(booked_revenue=("booked_revenue", "sum"))
            .reset_index()
        )
        model = attribution_summary.copy()
        model["reporting_month"] = pd.to_datetime(model["reporting_month"], errors="coerce")
        model = model.merge(actual, how="left", on="reporting_month").fillna({"booked_revenue": 0})
        for _, row in model.iterrows():
            variance = row["attributed_revenue"] - row["booked_revenue"]
            variance_rate = 0 if row["booked_revenue"] == 0 else variance / row["booked_revenue"]
            rows.append(
                {
                    "reporting_month": row["reporting_month"],
                    "normalized_channel": "all",
                    "comparison_type": f"{row['attribution_model']}_revenue_vs_booked",
                    "source_metric": "attributed_revenue",
                    "warehouse_metric": "booked_revenue",
                    "source_value": row["attributed_revenue"],
                    "warehouse_value": row["booked_revenue"],
                    "variance_value": variance,
                    "variance_rate": variance_rate,
                    "reconciliation_status": "reconciled" if abs(variance_rate) <= 0.10 else "model_variance",
                }
            )
    return pd.DataFrame(rows)


def _executive_briefing(
    executive_scorecard: pd.DataFrame,
    campaign_optimization: pd.DataFrame,
    regional_performance: pd.DataFrame,
    product_performance: pd.DataFrame,
    marketing_anomalies: pd.DataFrame,
    budget_pacing: pd.DataFrame,
    source_health: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    def add(priority: str, section: str, finding: str, recommended_action: str, evidence_metric: str) -> None:
        rows.append(
            {
                "priority": priority,
                "section": section,
                "finding": finding,
                "recommended_action": recommended_action,
                "evidence_metric": evidence_metric,
            }
        )

    if not executive_scorecard.empty:
        score = executive_scorecard.iloc[0]
        add(
            "P0",
            "Executive Scorecard",
            str(score.get("board_narrative", "No executive narrative generated.")),
            str(score.get("executive_status", "review")).replace("_", " ").title(),
            f"ROAS {float(score.get('roas', 0)):.2f}x, CAC ${float(score.get('cac', 0)):,.0f}",
        )

    if not campaign_optimization.empty:
        scale = campaign_optimization[campaign_optimization["recommended_action"].eq("scale")].head(1)
        reduce = campaign_optimization[campaign_optimization["recommended_action"].isin(["reduce", "pause_or_rebuild"])].head(1)
        if not scale.empty:
            row = scale.iloc[0]
            add(
                "P1",
                "Campaign Optimization",
                f"{row['campaign_name']} is the strongest budget expansion candidate.",
                "Increase budget on this campaign and monitor marginal CAC.",
                f"Attributed ROAS {float(row['attributed_roas']):.2f}x",
            )
        if not reduce.empty:
            row = reduce.iloc[0]
            add(
                "P1",
                "Campaign Optimization",
                f"{row['campaign_name']} is consuming budget with weak return.",
                str(row["recommended_action"]).replace("_", " ").title(),
                f"Spend ${float(row['spend']):,.0f}, ROAS {float(row['attributed_roas']):.2f}x",
            )

    if not regional_performance.empty:
        region = regional_performance.sort_values("booked_revenue", ascending=False).iloc[0]
        add(
            "P2",
            "Regional Performance",
            f"{region['region']} is the largest revenue market for {region['normalized_channel']}.",
            str(region["market_status"]).replace("_", " ").title(),
            f"Revenue ${float(region['booked_revenue']):,.0f}, margin rate {float(region['margin_rate']):.1%}",
        )

    if not product_performance.empty:
        product = product_performance.iloc[0]
        add(
            "P2",
            "Product Performance",
            f"{product['product']} has the highest booked revenue in the current demo mart.",
            str(product["product_priority"]).replace("_", " ").title(),
            f"Revenue ${float(product['booked_revenue']):,.0f}, margin rate {float(product['margin_rate']):.1%}",
        )

    if not marketing_anomalies.empty:
        anomaly = marketing_anomalies.iloc[0]
        add(
            "P0" if anomaly["severity"] == "high" else "P1",
            "Anomaly Detection",
            str(anomaly["investigation_hint"]),
            "Review upstream loads, campaign changes, and attribution joins.",
            f"{anomaly['metric_name']} z-score {float(anomaly['z_score']):.2f}",
        )

    if not budget_pacing.empty:
        pacing = budget_pacing.sort_values("efficiency_score", ascending=True).iloc[0]
        add(
            "P1",
            "Budget Pacing",
            f"{pacing['channel']} has the weakest pacing efficiency signal.",
            str(pacing["pacing_status"]).replace("_", " ").title(),
            f"Revenue attainment {float(pacing['revenue_attainment']):.1%}",
        )

    if not source_health.empty:
        unhealthy = source_health[source_health["source_health_status"].ne("healthy")]
        if not unhealthy.empty:
            source = unhealthy.iloc[0]
            add(
                "P0",
                "Source Reliability",
                f"{source['source_system']} needs source-health review.",
                str(source["source_health_status"]).replace("_", " ").title(),
                f"Rejected rate {float(source['rejection_rate']):.1%}",
            )

    return pd.DataFrame(rows)


def _performance_forecast(channel_perf: pd.DataFrame) -> pd.DataFrame:
    if channel_perf.empty:
        return pd.DataFrame()
    frame = channel_perf.copy()
    frame["reporting_month"] = pd.to_datetime(frame["reporting_month"], errors="coerce")
    metrics = ["spend", "booked_revenue", "gross_margin", "leads", "closed_won_conversions"]
    for column in metrics:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)

    rows = []
    for channel_name, group in frame.groupby("normalized_channel", dropna=False):
        group = group.sort_values("reporting_month")
        if group.empty or group["reporting_month"].isna().all():
            continue
        latest_month = group["reporting_month"].max()
        recent = group.tail(3)
        metric_forecasts = {}
        for metric in metrics:
            values = recent[metric].astype(float).tolist()
            baseline = float(np.mean(values)) if values else 0.0
            trend = 0.0
            if len(values) > 1:
                trend = (values[-1] - values[0]) / max(1, len(values) - 1)
            metric_forecasts[metric] = (baseline, trend)

        for horizon in range(1, 4):
            forecast_month = latest_month + pd.DateOffset(months=horizon)
            row = {
                "forecast_month": forecast_month,
                "normalized_channel": channel_name,
                "forecast_horizon_months": horizon,
                "forecast_method": "rolling_3_month_trend",
            }
            for metric, (baseline, trend) in metric_forecasts.items():
                forecast_value = max(0.0, baseline + (trend * horizon * 0.65))
                row[f"forecast_{metric}"] = forecast_value
                row[f"{metric}_low"] = forecast_value * (1 - 0.10 - (horizon * 0.03))
                row[f"{metric}_high"] = forecast_value * (1 + 0.10 + (horizon * 0.03))
            row["forecast_roas"] = 0 if row["forecast_spend"] == 0 else row["forecast_booked_revenue"] / row["forecast_spend"]
            row["forecast_cac"] = (
                0
                if row["forecast_closed_won_conversions"] == 0
                else row["forecast_spend"] / row["forecast_closed_won_conversions"]
            )
            row["forecast_margin_rate"] = (
                0 if row["forecast_booked_revenue"] == 0 else row["forecast_gross_margin"] / row["forecast_booked_revenue"]
            )
            row["forecast_confidence"] = "medium" if len(recent) >= 3 else "low"
            rows.append(row)
    return pd.DataFrame(rows)


def _budget_scenarios(channel_perf: pd.DataFrame, campaign_optimization: pd.DataFrame) -> pd.DataFrame:
    if channel_perf.empty:
        return pd.DataFrame()
    frame = channel_perf.copy()
    for column in ["spend", "booked_revenue", "gross_margin", "leads", "closed_won_conversions"]:
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0)
    channel = (
        frame.groupby("normalized_channel", dropna=False)
        .agg(
            current_spend=("spend", "sum"),
            current_revenue=("booked_revenue", "sum"),
            current_margin=("gross_margin", "sum"),
            current_leads=("leads", "sum"),
            current_conversions=("closed_won_conversions", "sum"),
        )
        .reset_index()
    )
    channel["base_roas"] = safe_divide(channel["current_revenue"], channel["current_spend"])
    channel["base_margin_rate"] = safe_divide(channel["current_margin"], channel["current_revenue"])
    channel["base_cac"] = safe_divide(channel["current_spend"], channel["current_conversions"])

    recommended = pd.DataFrame(columns=["normalized_channel", "recommended_shift_pct"])
    if not campaign_optimization.empty:
        opt = campaign_optimization.copy()
        for column in ["spend", "recommended_monthly_budget"]:
            opt[column] = pd.to_numeric(opt.get(column, 0), errors="coerce").fillna(0)
        recommended = (
            opt.groupby("normalized_channel", dropna=False)
            .agg(current_campaign_spend=("spend", "sum"), recommended_campaign_spend=("recommended_monthly_budget", "sum"))
            .reset_index()
        )
        recommended["recommended_shift_pct"] = safe_divide(
            recommended["recommended_campaign_spend"] - recommended["current_campaign_spend"],
            recommended["current_campaign_spend"],
        ).clip(-0.5, 0.5)
        recommended = recommended[["normalized_channel", "recommended_shift_pct"]]

    channel = channel.merge(recommended, how="left", on="normalized_channel").fillna({"recommended_shift_pct": 0.0})
    scenario_specs = [
        ("baseline", 0.0, 1.00, "Hold current budget and monitor efficiency."),
        ("conservative_cut", -0.10, 1.05, "Reduce budget and preserve the most efficient demand."),
        ("recommended_mix", None, 0.95, "Apply campaign-level scale/reduce recommendations."),
        ("aggressive_growth", 0.20, 0.85, "Increase budget with a diminishing-return assumption."),
    ]
    rows = []
    for _, row in channel.iterrows():
        base_roas = float(row["base_roas"])
        margin_rate = float(row["base_margin_rate"]) if row["base_margin_rate"] > 0 else 0.45
        lead_rate = 0 if row["current_spend"] == 0 else row["current_leads"] / row["current_spend"]
        conversion_rate = 0 if row["current_spend"] == 0 else row["current_conversions"] / row["current_spend"]
        for scenario_name, default_shift, marginal_multiplier, scenario_note in scenario_specs:
            shift = float(row["recommended_shift_pct"]) if default_shift is None else default_shift
            projected_spend = max(0.0, float(row["current_spend"]) * (1 + shift))
            spend_delta = projected_spend - float(row["current_spend"])
            projected_revenue = max(0.0, float(row["current_revenue"]) + spend_delta * base_roas * marginal_multiplier)
            projected_margin = projected_revenue * margin_rate
            projected_leads = max(0.0, float(row["current_leads"]) + spend_delta * lead_rate * (0.9 if spend_delta > 0 else 1.05))
            projected_conversions = max(
                0.0,
                float(row["current_conversions"]) + spend_delta * conversion_rate * (0.9 if spend_delta > 0 else 1.05),
            )
            projected_roas = 0 if projected_spend == 0 else projected_revenue / projected_spend
            projected_cac = 0 if projected_conversions == 0 else projected_spend / projected_conversions
            decision = "hold"
            if projected_margin - float(row["current_margin"]) > 0 and projected_roas >= max(1.0, base_roas * 0.85):
                decision = "approve"
            if projected_roas < 1 or projected_margin < float(row["current_margin"]) * 0.85:
                decision = "reject_or_rework"
            rows.append(
                {
                    "scenario_name": scenario_name,
                    "normalized_channel": row["normalized_channel"],
                    "budget_shift_pct": shift,
                    "current_spend": row["current_spend"],
                    "projected_spend": projected_spend,
                    "projected_revenue": projected_revenue,
                    "projected_margin": projected_margin,
                    "projected_leads": projected_leads,
                    "projected_conversions": projected_conversions,
                    "projected_roas": projected_roas,
                    "projected_cac": projected_cac,
                    "incremental_revenue": projected_revenue - float(row["current_revenue"]),
                    "incremental_margin": projected_margin - float(row["current_margin"]),
                    "decision": decision,
                    "scenario_note": scenario_note,
                }
            )
    return pd.DataFrame(rows)


def _customer_cohort_retention(leads: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    if leads.empty:
        return pd.DataFrame()
    lead_frame = leads.copy()
    lead_frame["created_at"] = pd.to_datetime(lead_frame.get("created_at"), errors="coerce")
    lead_frame["cohort_month"] = lead_frame["created_at"].dt.to_period("M").dt.to_timestamp()
    lead_frame["normalized_channel"] = lead_frame.get("lead_source", "unknown").map(normalize_channel)
    lead_frame["customer_id"] = lead_frame.get("customer_id", "UNKNOWN").fillna("UNKNOWN")
    cohort_size = (
        lead_frame.groupby(["cohort_month", "normalized_channel"], dropna=False)
        .agg(cohort_customers=("customer_id", "nunique"), cohort_leads=("lead_id", "count"))
        .reset_index()
    )
    if sales.empty:
        cohort_size["activity_month"] = cohort_size["cohort_month"]
        cohort_size["months_since_cohort"] = 0
        cohort_size["active_customers"] = 0
        cohort_size["conversions"] = 0
        cohort_size["booked_revenue"] = 0.0
        cohort_size["gross_margin"] = 0.0
        cohort_size["retention_rate"] = 0.0
        cohort_size["revenue_per_cohort_customer"] = 0.0
        return cohort_size

    sale_frame = sales.copy()
    sale_frame["conversion_date"] = pd.to_datetime(sale_frame.get("conversion_date"), errors="coerce")
    sale_frame["activity_month"] = sale_frame["conversion_date"].dt.to_period("M").dt.to_timestamp()
    sale_frame["deal_value"] = pd.to_numeric(sale_frame.get("deal_value", 0), errors="coerce").fillna(0)
    sale_frame["gross_margin"] = pd.to_numeric(sale_frame.get("gross_margin", 0), errors="coerce").fillna(0)
    lead_lookup = lead_frame[["lead_id", "customer_id", "cohort_month", "normalized_channel"]].drop_duplicates("lead_id")
    joined = sale_frame.merge(lead_lookup, how="left", on="lead_id", suffixes=("", "_lead"))
    joined["customer_id"] = joined["customer_id_lead"].combine_first(joined.get("customer_id"))
    joined["cohort_month"] = joined["cohort_month"].fillna(joined["activity_month"])
    joined["normalized_channel"] = joined["normalized_channel"].fillna("unknown")
    joined["months_since_cohort"] = (
        (joined["activity_month"].dt.year - joined["cohort_month"].dt.year) * 12
        + (joined["activity_month"].dt.month - joined["cohort_month"].dt.month)
    ).clip(lower=0)
    activity = (
        joined.groupby(["cohort_month", "normalized_channel", "activity_month", "months_since_cohort"], dropna=False)
        .agg(
            active_customers=("customer_id", "nunique"),
            conversions=("conversion_id", "count"),
            booked_revenue=("deal_value", "sum"),
            gross_margin=("gross_margin", "sum"),
        )
        .reset_index()
    )
    result = activity.merge(cohort_size, how="left", on=["cohort_month", "normalized_channel"]).fillna(
        {"cohort_customers": 0, "cohort_leads": 0}
    )
    result["retention_rate"] = safe_divide(result["active_customers"], result["cohort_customers"])
    result["revenue_per_cohort_customer"] = safe_divide(result["booked_revenue"], result["cohort_customers"])
    result["margin_per_cohort_customer"] = safe_divide(result["gross_margin"], result["cohort_customers"])
    return result.sort_values(["cohort_month", "normalized_channel", "months_since_cohort"])


def _action_center(
    campaign_optimization: pd.DataFrame,
    budget_pacing: pd.DataFrame,
    marketing_anomalies: pd.DataFrame,
    source_health: pd.DataFrame,
    data_quality: pd.DataFrame,
    budget_scenarios: pd.DataFrame,
    performance_forecast: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    created_at = datetime.now(timezone.utc).isoformat()

    def add(
        priority: str,
        action_type: str,
        owner_team: str,
        source_area: str,
        normalized_channel: str,
        title: str,
        recommended_action: str,
        business_impact: str,
        evidence_metric: str,
        due_in_days: int,
        action_value: float,
    ) -> None:
        rows.append(
            {
                "priority": priority,
                "action_type": action_type,
                "owner_team": owner_team,
                "source_area": source_area,
                "normalized_channel": normalized_channel,
                "title": title,
                "recommended_action": recommended_action,
                "business_impact": business_impact,
                "evidence_metric": evidence_metric,
                "due_in_days": due_in_days,
                "action_value": action_value,
                "status": "open",
                "created_at": created_at,
            }
        )

    if not campaign_optimization.empty:
        optimization = campaign_optimization.copy()
        for column in ["spend", "recommended_monthly_budget", "attributed_roas", "opportunity_score"]:
            optimization[column] = pd.to_numeric(optimization.get(column, 0), errors="coerce").fillna(0)
        focus = optimization[
            optimization["recommended_action"].isin(["scale", "reduce", "pause_or_rebuild"])
        ].sort_values(["opportunity_score", "spend"], ascending=[False, False]).head(10)
        for _, row in focus.iterrows():
            action = str(row["recommended_action"])
            priority = "P1" if action == "scale" else "P0"
            budget_delta = float(row["recommended_monthly_budget"] - row["spend"])
            add(
                priority=priority,
                action_type="campaign_budget",
                owner_team="growth_marketing",
                source_area="campaign_optimization",
                normalized_channel=str(row["normalized_channel"]),
                title=f"{action.replace('_', ' ').title()} {row['campaign_name']}",
                recommended_action=str(row["optimization_reason"]),
                business_impact=f"Recommended monthly budget delta ${budget_delta:,.0f}.",
                evidence_metric=f"ROAS {float(row['attributed_roas']):.2f}x, spend ${float(row['spend']):,.0f}.",
                due_in_days=7 if priority == "P1" else 2,
                action_value=abs(budget_delta),
            )

    if not budget_pacing.empty:
        pacing = budget_pacing.copy()
        pacing["revenue_gap"] = pd.to_numeric(pacing.get("revenue_gap", 0), errors="coerce").fillna(0)
        pacing["revenue_attainment"] = pd.to_numeric(pacing.get("revenue_attainment", 0), errors="coerce").fillna(0)
        focus = pacing[pacing["pacing_status"].isin(["overspending_underperforming", "under_pacing"])].head(8)
        for _, row in focus.iterrows():
            add(
                priority="P1",
                action_type="budget_pacing",
                owner_team="growth_finance",
                source_area="target_vs_actual",
                normalized_channel=str(row["channel"]),
                title=f"Resolve {row['channel']} pacing risk",
                recommended_action=f"Review budget owner {row['budget_owner']} and rebalance plan.",
                business_impact=f"Revenue gap ${float(row['revenue_gap']):,.0f}.",
                evidence_metric=f"Revenue attainment {float(row['revenue_attainment']):.1%}.",
                due_in_days=5,
                action_value=abs(float(row["revenue_gap"])),
            )

    if not marketing_anomalies.empty:
        anomalies = marketing_anomalies.copy()
        anomalies["pct_change"] = pd.to_numeric(anomalies.get("pct_change", 0), errors="coerce").fillna(0)
        anomalies["z_score"] = pd.to_numeric(anomalies.get("z_score", 0), errors="coerce").fillna(0)
        focus = anomalies.sort_values(["severity", "z_score"], ascending=[True, False]).head(8)
        for _, row in focus.iterrows():
            severity = str(row["severity"])
            add(
                priority="P0" if severity == "high" else "P1",
                action_type="anomaly_investigation",
                owner_team="analytics_engineering",
                source_area="anomaly_center",
                normalized_channel=str(row["normalized_channel"]),
                title=f"Investigate {row['metric_name']} anomaly",
                recommended_action=str(row["investigation_hint"]),
                business_impact="Potential dashboard variance or material business shift.",
                evidence_metric=f"z-score {float(row['z_score']):.2f}, change {float(row['pct_change']):.1%}.",
                due_in_days=1 if severity == "high" else 3,
                action_value=abs(float(row["z_score"])) + abs(float(row["pct_change"])),
            )

    if not source_health.empty:
        health = source_health[source_health["source_health_status"].ne("healthy")].copy()
        health["rejection_rate"] = pd.to_numeric(health.get("rejection_rate", 0), errors="coerce").fillna(0)
        for _, row in health.iterrows():
            add(
                priority="P0" if row["source_health_status"] == "attention" else "P1",
                action_type="source_reliability",
                owner_team="data_engineering",
                source_area="source_health",
                normalized_channel="all",
                title=f"Fix {row['source_system']} source health",
                recommended_action="Review ingestion audit, rejected rows, and source contract drift.",
                business_impact=f"{int(row['rejected'])} rejected rows can affect downstream marts.",
                evidence_metric=f"Acceptance {float(row['acceptance_rate']):.1%}, rejection {float(row['rejection_rate']):.1%}.",
                due_in_days=1,
                action_value=float(row["rejected"]) + float(row["quality_issue_count"]),
            )

    if not data_quality.empty:
        quality = data_quality[data_quality["monitoring_status"].ne("healthy")].copy()
        quality["rejected_rate"] = pd.to_numeric(quality.get("rejected_rate", 0), errors="coerce").fillna(0)
        quality["issue_count"] = pd.to_numeric(quality.get("issue_count", 0), errors="coerce").fillna(0)
        for _, row in quality.head(8).iterrows():
            add(
                priority="P0" if row["monitoring_status"] == "quality_failure" else "P1",
                action_type="data_quality",
                owner_team="analytics_engineering",
                source_area="quality_monitoring",
                normalized_channel="all",
                title=f"Review quality checks for {row['source_system']}",
                recommended_action="Inspect failing rows, update mappings, or confirm acceptable source drift.",
                business_impact="Quality failures can break executive and analyst trust.",
                evidence_metric=f"{int(row['issue_count'])} issues, rejected rate {float(row['rejected_rate']):.1%}.",
                due_in_days=2,
                action_value=float(row["issue_count"]) + float(row["rejected_rate"]),
            )

    if not budget_scenarios.empty:
        scenarios = budget_scenarios.copy()
        scenarios["incremental_margin"] = pd.to_numeric(scenarios.get("incremental_margin", 0), errors="coerce").fillna(0)
        scenarios["projected_roas"] = pd.to_numeric(scenarios.get("projected_roas", 0), errors="coerce").fillna(0)
        focus = scenarios[
            scenarios["decision"].eq("approve") & scenarios["scenario_name"].isin(["recommended_mix", "aggressive_growth"])
        ].sort_values("incremental_margin", ascending=False).head(5)
        for _, row in focus.iterrows():
            add(
                priority="P2",
                action_type="planning_approval",
                owner_team="marketing_leadership",
                source_area="scenario_planning",
                normalized_channel=str(row["normalized_channel"]),
                title=f"Approve {row['scenario_name']} scenario for {row['normalized_channel']}",
                recommended_action=str(row["scenario_note"]),
                business_impact=f"Projected incremental margin ${float(row['incremental_margin']):,.0f}.",
                evidence_metric=f"Projected ROAS {float(row['projected_roas']):.2f}x.",
                due_in_days=14,
                action_value=max(0.0, float(row["incremental_margin"])),
            )

    if not performance_forecast.empty:
        forecast = performance_forecast.copy()
        forecast["forecast_roas"] = pd.to_numeric(forecast.get("forecast_roas", 0), errors="coerce").fillna(0)
        forecast["forecast_cac"] = pd.to_numeric(forecast.get("forecast_cac", 0), errors="coerce").fillna(0)
        focus = forecast[(forecast["forecast_roas"] < 1) & (forecast["forecast_spend"] > 0)].head(6)
        for _, row in focus.iterrows():
            add(
                priority="P2",
                action_type="forecast_risk",
                owner_team="growth_marketing",
                source_area="performance_forecast",
                normalized_channel=str(row["normalized_channel"]),
                title=f"Mitigate forecast ROAS risk for {row['normalized_channel']}",
                recommended_action="Use scenario planner to reduce weak spend or improve conversion rate assumptions.",
                business_impact=f"Forecast ROAS below 1.0 for horizon {int(row['forecast_horizon_months'])}.",
                evidence_metric=f"Forecast ROAS {float(row['forecast_roas']):.2f}x, CAC ${float(row['forecast_cac']):,.0f}.",
                due_in_days=10,
                action_value=max(0.0, 1 - float(row["forecast_roas"])),
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "action_id",
                "priority",
                "action_type",
                "owner_team",
                "source_area",
                "normalized_channel",
                "title",
                "recommended_action",
                "business_impact",
                "evidence_metric",
                "due_in_days",
                "action_value",
                "status",
                "created_at",
            ]
        )
    action_center = pd.DataFrame(rows)
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    action_center["priority_rank"] = action_center["priority"].map(priority_rank).fillna(9)
    action_center = action_center.sort_values(["priority_rank", "due_in_days", "action_value"], ascending=[True, True, False])
    action_center.insert(0, "action_id", [f"ACT-{index + 1:04d}" for index in range(len(action_center))])
    return action_center.drop(columns=["priority_rank"])


def _score_status(score: float) -> str:
    if score >= 90:
        return "healthy"
    if score >= 70:
        return "watch"
    return "at_risk"


def _data_product_scorecard(
    source_health: pd.DataFrame,
    data_quality: pd.DataFrame,
    action_center: pd.DataFrame,
    executive_scorecard: pd.DataFrame,
    journey_quality: pd.DataFrame,
    attribution_reconciliation: pd.DataFrame,
    performance_forecast: pd.DataFrame,
    budget_scenarios: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "scorecard_domain",
        "owner_team",
        "service_level_indicator",
        "current_value",
        "target_value",
        "score",
        "score_status",
        "risk_count",
        "evidence",
        "next_action",
        "dashboard_surface",
    ]
    rows: list[dict] = []

    def add(
        domain: str,
        owner: str,
        sli: str,
        current_value: str,
        target_value: str,
        score: float,
        risk_count: int,
        evidence: str,
        next_action: str,
        surface: str,
    ) -> None:
        bounded_score = max(0, min(100, round(float(score), 1)))
        rows.append(
            {
                "scorecard_domain": domain,
                "owner_team": owner,
                "service_level_indicator": sli,
                "current_value": current_value,
                "target_value": target_value,
                "score": bounded_score,
                "score_status": _score_status(bounded_score),
                "risk_count": int(risk_count),
                "evidence": evidence,
                "next_action": next_action,
                "dashboard_surface": surface,
            }
        )

    if source_health.empty:
        add(
            "Source Reliability",
            "data_engineering",
            "Accepted records across active sources",
            "0.0%",
            ">= 98.0%",
            0,
            1,
            "No source-health rows were generated.",
            "Run ingestion and validate source audit logs.",
            "Diagnostics",
        )
    else:
        health = source_health.copy()
        for column in ["accepted", "rows", "rejected", "quality_issue_count", "acceptance_rate", "rejection_rate"]:
            health[column] = pd.to_numeric(health.get(column, 0), errors="coerce").fillna(0)
        accepted = float(health["accepted"].sum())
        total_rows = float(health["rows"].sum())
        acceptance_rate = 0 if total_rows == 0 else accepted / total_rows
        unhealthy = int(health["source_health_status"].ne("healthy").sum())
        add(
            "Source Reliability",
            "data_engineering",
            "Accepted records across active sources",
            f"{acceptance_rate:.1%}",
            ">= 98.0%",
            acceptance_rate * 100,
            unhealthy,
            f"{int(health['rejected'].sum()):,} rejected rows across {len(health):,} sources.",
            "Review source contracts, rejected-row files, and API retry history.",
            "Diagnostics",
        )
        watermark_coverage = health["latest_watermark"].notna().mean() if "latest_watermark" in health.columns else 0
        add(
            "Incremental Readiness",
            "data_engineering",
            "Sources with captured high-watermark metadata",
            f"{watermark_coverage:.1%}",
            "100.0%",
            watermark_coverage * 100,
            int(len(health) - health["latest_watermark"].notna().sum()) if "latest_watermark" in health.columns else len(health),
            "Watermarks determine whether incremental runs can continue without duplicate processing.",
            "Backfill missing watermarks before production-like reruns.",
            "Diagnostics",
        )

    if data_quality.empty:
        add(
            "Data Quality",
            "analytics_engineering",
            "Quality checks passing without warning/failure status",
            "0.0%",
            ">= 95.0%",
            0,
            1,
            "No data-quality summary was available.",
            "Generate quality reports before certifying marts.",
            "Quality",
        )
    else:
        quality = data_quality.copy()
        for column in ["row_count", "rejected_count", "issue_count", "rejected_rate"]:
            quality[column] = pd.to_numeric(quality.get(column, 0), errors="coerce").fillna(0)
        pass_rate = quality["monitoring_status"].eq("healthy").mean()
        warning_count = int(quality["monitoring_status"].isin(["quality_warning", "quality_failure"]).sum())
        rejected_rate = 0 if quality["row_count"].sum() == 0 else quality["rejected_count"].sum() / quality["row_count"].sum()
        add(
            "Data Quality",
            "analytics_engineering",
            "Quality checks passing without warning/failure status",
            f"{pass_rate:.1%}",
            ">= 95.0%",
            pass_rate * 100,
            warning_count,
            f"Aggregate rejected-row rate is {rejected_rate:.1%}.",
            "Clear warning/failure rows or document accepted source drift.",
            "Quality",
        )

    if journey_quality.empty:
        add(
            "Journey Stitching",
            "analytics_engineering",
            "Attribution coverage for lead and conversion records",
            "0.0%",
            ">= 90.0%",
            0,
            1,
            "No journey-quality mart was available.",
            "Rebuild journey diagnostics after source ingestion.",
            "Diagnostics",
        )
    else:
        journey = journey_quality.copy()
        for column in ["attribution_coverage", "orphan_conversion_rate"]:
            journey[column] = pd.to_numeric(journey.get(column, 0), errors="coerce").fillna(0)
        attribution_coverage = float(journey["attribution_coverage"].mean())
        orphan_rate = float(journey["orphan_conversion_rate"].max())
        risk_count = int(journey["journey_health_status"].ne("healthy").sum())
        add(
            "Journey Stitching",
            "analytics_engineering",
            "Attribution coverage for lead and conversion records",
            f"{attribution_coverage:.1%}",
            ">= 90.0%",
            attribution_coverage * 100,
            risk_count,
            f"Maximum orphan-conversion rate is {orphan_rate:.1%}.",
            "Resolve missing attribution IDs and orphan conversion joins.",
            "Diagnostics",
        )

    if attribution_reconciliation.empty:
        add(
            "Attribution Reconciliation",
            "analytics_engineering",
            "Attribution comparisons reconciled within tolerance",
            "0.0%",
            ">= 85.0%",
            0,
            1,
            "No attribution reconciliation rows were generated.",
            "Generate attribution comparison marts and investigate model variance.",
            "Attribution",
        )
    else:
        reconciliation = attribution_reconciliation.copy()
        reconciled_rate = reconciliation["reconciliation_status"].eq("reconciled").mean()
        risk_count = int(reconciliation["reconciliation_status"].ne("reconciled").sum())
        add(
            "Attribution Reconciliation",
            "analytics_engineering",
            "Attribution comparisons reconciled within tolerance",
            f"{reconciled_rate:.1%}",
            ">= 85.0%",
            reconciled_rate * 100,
            risk_count,
            f"{risk_count:,} model or platform variances need explanation.",
            "Attach reconciliation notes to ROI dashboard pages.",
            "Attribution",
        )

    if action_center.empty:
        add(
            "Action Management",
            "marketing_operations",
            "Critical open actions under SLA",
            "No open actions",
            "0 overdue P0/P1",
            100,
            0,
            "Action queue is empty.",
            "Continue monitoring owner workload and new quality signals.",
            "Action Center",
        )
    else:
        actions = action_center.copy()
        actions["due_in_days"] = pd.to_numeric(actions.get("due_in_days", 0), errors="coerce").fillna(0)
        critical = actions["priority"].isin(["P0", "P1"])
        urgent_critical = int((critical & (actions["due_in_days"] <= 2)).sum())
        critical_count = int(critical.sum())
        score = max(0, 100 - urgent_critical * 12 - max(0, critical_count - 10) * 3)
        add(
            "Action Management",
            "marketing_operations",
            "Critical open actions under SLA",
            f"{urgent_critical:,} urgent P0/P1",
            "0 overdue P0/P1",
            score,
            urgent_critical,
            f"{critical_count:,} total P0/P1 actions assigned across {actions['owner_team'].nunique():,} teams.",
            "Triage P0 actions first, then balance owner-team workload.",
            "Action Center",
        )

    if executive_scorecard.empty:
        add(
            "Executive Confidence",
            "revenue_operations",
            "Executive scorecard publish readiness",
            "Unavailable",
            "Published and explainable",
            0,
            1,
            "No executive scorecard row was available.",
            "Rebuild marts and review KPI dependencies.",
            "Executive",
        )
    else:
        score = executive_scorecard.iloc[0]
        status = str(score.get("executive_status", "unknown"))
        status_score = {"scale": 100, "optimize": 88, "profitability_watch": 68, "data_risk": 45}.get(status, 60)
        risk_count = int(status in {"profitability_watch", "data_risk"})
        add(
            "Executive Confidence",
            "revenue_operations",
            "Executive scorecard publish readiness",
            status.replace("_", " ").title(),
            "Scale or Optimize",
            status_score,
            risk_count,
            str(score.get("board_narrative", "No narrative generated.")),
            "Use the briefing and action queue to explain the current status.",
            "Executive",
        )

    planning_rows = len(performance_forecast) + len(budget_scenarios)
    approved_scenarios = 0 if budget_scenarios.empty else int(budget_scenarios["decision"].eq("approve").sum())
    planning_score = 100 if planning_rows and approved_scenarios else (70 if planning_rows else 0)
    add(
        "Planning Readiness",
        "growth_finance",
        "Forecast and scenario outputs available for planning",
        f"{planning_rows:,} planning rows",
        "Forecast plus approved scenarios",
        planning_score,
        0 if approved_scenarios else 1,
        f"{approved_scenarios:,} approved budget scenarios generated.",
        "Review recommended_mix and aggressive_growth decisions before budget changes.",
        "Planning",
    )

    return pd.DataFrame(rows, columns=columns)


def _semantic_kpi_governance() -> pd.DataFrame:
    columns = [
        "kpi_name",
        "business_definition",
        "formula",
        "grain",
        "owner_team",
        "certified_status",
        "source_marts",
        "dashboard_pages",
        "target_or_guardrail",
        "dax_measure_name",
        "quality_dependencies",
        "refresh_sla",
        "interpretation_notes",
    ]
    rows = [
        (
            "ROAS",
            "Revenue returned for each marketing dollar spent.",
            "booked_revenue / spend",
            "month, channel, campaign",
            "revenue_operations",
            "certified",
            "mart_channel_performance, mart_campaign_performance",
            "Executive, Channels, Optimization",
            ">= 3.0x for scale decisions",
            "ROAS",
            "spend non-null, revenue reconciled, campaign mapping current",
            "daily by 8:00 AM local",
            "Use booked revenue for executive reporting; platform conversions are a diagnostic input.",
        ),
        (
            "CAC",
            "Marketing spend required to create one closed-won conversion.",
            "spend / closed_won_conversions",
            "month, channel",
            "revenue_operations",
            "certified",
            "mart_channel_performance",
            "Executive, Channels, Planning",
            "Below product-level payback threshold",
            "CAC",
            "closed-won conversions loaded, no orphan conversion spike",
            "daily by 8:00 AM local",
            "Do not compare CAC across channels without checking conversion lag.",
        ),
        (
            "Marketing Efficiency Ratio",
            "Gross margin generated per marketing dollar spent.",
            "gross_margin / spend",
            "month, channel",
            "growth_finance",
            "certified",
            "mart_channel_performance, mart_budget_efficiency",
            "Executive, Targets, Planning",
            ">= 1.0x margin coverage",
            "Marketing Efficiency Ratio",
            "gross margin present, spend validated",
            "daily by 8:00 AM local",
            "Preferred for budget decisions when margin varies by product.",
        ),
        (
            "Lead to Close Rate",
            "Share of captured leads that become closed-won conversions.",
            "closed_won_conversions / leads",
            "month, channel",
            "sales_operations",
            "certified",
            "mart_channel_performance, mart_funnel_performance",
            "Executive, Funnel, Diagnostics",
            "Stable or improving month over month",
            "Lead to Close Rate",
            "lead IDs unique, conversion joins valid",
            "daily by 8:00 AM local",
            "A falling rate may be caused by source mix, handoff issues, or late-arriving revenue.",
        ),
        (
            "Attribution Coverage",
            "Share of journey records with usable attribution identifiers.",
            "1 - missing_attribution_records / measurable_records",
            "channel",
            "analytics_engineering",
            "certified",
            "mart_journey_quality",
            "Diagnostics, Governance",
            ">= 90.0%",
            "Attribution Coverage",
            "attribution_id populated, session campaign mapping valid",
            "daily by 8:00 AM local",
            "Coverage below target should be shown before ROI conclusions.",
        ),
        (
            "Target Attainment",
            "Actual performance divided by monthly business target.",
            "actual_metric / target_metric",
            "month, channel, region, budget_owner",
            "growth_finance",
            "certified",
            "mart_target_vs_actual, mart_budget_pacing",
            "Targets, Executive",
            "Revenue attainment >= 100% with spend attainment <= 105%",
            "Revenue Attainment",
            "target file loaded, month alignment valid",
            "daily by 8:00 AM local",
            "Spend attainment alone is not success; pair it with revenue and lead attainment.",
        ),
        (
            "Forecast ROAS",
            "Expected revenue efficiency over the next three planning months.",
            "forecast_booked_revenue / forecast_spend",
            "forecast_month, channel",
            "growth_finance",
            "candidate",
            "mart_performance_forecast",
            "Planning",
            ">= current channel ROAS * 0.85",
            "Forecast ROAS",
            "three months of history preferred",
            "daily by 8:00 AM local",
            "Uses a simple rolling trend for local scenario planning; replace with a production forecasting service if needed.",
        ),
        (
            "Data Product Score",
            "Operating-health score for source reliability, quality, attribution, and BI readiness.",
            "weighted operational score by domain",
            "scorecard_domain",
            "data_product_owner",
            "certified",
            "mart_data_product_scorecard",
            "Governance",
            ">= 90 healthy, 70-89 watch",
            "Data Product Score",
            "source health, quality, action center, reconciliation marts",
            "daily by 8:00 AM local",
            "Use this as the release gate for executive-facing dashboard changes.",
        ),
        (
            "Open Critical Actions",
            "Count of P0/P1 actions requiring owner-team follow-up.",
            "count actions where priority in P0/P1",
            "owner_team, priority",
            "marketing_operations",
            "certified",
            "mart_action_center",
            "Action Center, Governance",
            "0 overdue P0/P1 actions",
            "Open Critical Actions",
            "action center generated from quality, forecast, anomaly, and pacing marts",
            "daily by 8:00 AM local",
            "Prioritize operational trust issues before budget-expansion decisions.",
        ),
    ]
    return pd.DataFrame(rows, columns=columns)


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Build BI demo marts from local raw lake files.").parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(build_demo_marts(), indent=2, default=str))


if __name__ == "__main__":
    main()
