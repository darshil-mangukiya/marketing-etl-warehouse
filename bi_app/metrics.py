from __future__ import annotations

import math
from typing import Any

import pandas as pd


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator in (0, 0.0) or pd.isna(denominator):
        return 0.0
    return float(numerator) / float(denominator)


def sum_column(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def count_rows(frame: pd.DataFrame) -> int:
    return int(len(frame)) if not frame.empty else 0


def fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def fmt_number(value: float) -> str:
    return f"{value:,.0f}"


def fmt_ratio(value: float) -> str:
    return f"{value:,.2f}x"


def fmt_percent(value: float) -> str:
    return f"{value:.1%}"


def executive_kpis(
    channel: pd.DataFrame,
    target: pd.DataFrame,
    quality: pd.DataFrame,
    source_health: pd.DataFrame,
) -> dict[str, Any]:
    # kpi_catalog_key: total_spend, booked_revenue, roas, cac, revenue_attainment
    spend = sum_column(channel, "spend")
    revenue = sum_column(channel, "booked_revenue")
    leads = sum_column(channel, "leads")
    conversions = sum_column(channel, "closed_won_conversions")
    target_revenue = sum_column(target, "target_revenue")
    actual_revenue = sum_column(target, "actual_revenue") or revenue

    return {
        "total_spend": spend,
        "total_revenue": revenue,
        "roas": safe_divide(revenue, spend),
        "cac": safe_divide(spend, conversions),
        "leads": leads,
        "conversions": conversions,
        "target_attainment": safe_divide(actual_revenue, target_revenue),
        "data_quality_status": data_quality_status(quality, source_health),
    }


def data_quality_status(quality: pd.DataFrame, source_health: pd.DataFrame) -> str:
    statuses: set[str] = set()
    if not quality.empty and "monitoring_status" in quality.columns:
        statuses.update(str(value).lower() for value in quality["monitoring_status"].dropna().unique())
    if not source_health.empty and "source_health_status" in source_health.columns:
        statuses.update(str(value).lower() for value in source_health["source_health_status"].dropna().unique())
    if not statuses:
        return "Unknown"
    if any("fail" in status or "critical" in status for status in statuses):
        return "Needs Review"
    if any("warning" in status or "attention" in status or "risk" in status for status in statuses):
        return "Watch"
    return "Healthy"


def campaign_recommendation(row: pd.Series | dict[str, Any], median_spend: float = 0.0) -> str:
    roas = _float_value(row, "attributed_roas", "roas")
    spend = _float_value(row, "spend")
    conversions = _float_value(row, "conversions", "closed_won_conversions")
    waste_flag = _bool_value(row, "waste_budget_flag")
    attributed_revenue = _float_value(row, "attributed_revenue", "booked_revenue")
    has_revenue_field = _has_any_key(row, "attributed_revenue", "booked_revenue")

    if waste_flag or (median_spend > 0 and spend > median_spend and roas < 0.75):
        return "Pause Candidate"
    if roas >= 2.0 and conversions >= 10:
        return "Scale"
    if roas < 1.25 or (has_revenue_field and conversions > 0 and attributed_revenue <= 0):
        return "Optimize"
    return "Monitor"


def campaign_quality_flags(row: pd.Series | dict[str, Any]) -> str:
    flags: list[str] = []
    if _bool_value(row, "waste_budget_flag"):
        flags.append("waste_budget")
    conversions = _float_value(row, "conversions", "closed_won_conversions")
    attributed_revenue = _float_value(row, "attributed_revenue", "booked_revenue")
    if _has_any_key(row, "attributed_revenue", "booked_revenue") and conversions > 0 and attributed_revenue <= 0:
        flags.append("missing_attribution")
    if _float_value(row, "spend") <= 0 and conversions > 0:
        flags.append("zero_spend_with_conversions")
    return ", ".join(flags) if flags else "none"


def add_campaign_recommendations(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    output = frame.copy()
    median_spend = float(pd.to_numeric(output.get("spend", pd.Series(dtype=float)), errors="coerce").median())
    if math.isnan(median_spend):
        median_spend = 0.0
    output["recommendation_label"] = output.apply(
        lambda row: campaign_recommendation(row, median_spend=median_spend),
        axis=1,
    )
    output["data_quality_flags"] = output.apply(campaign_quality_flags, axis=1)
    return output


def channel_rollup(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "normalized_channel" not in frame.columns:
        return pd.DataFrame()

    group_cols = ["normalized_channel"]
    if "channel_name" in frame.columns:
        group_cols.append("channel_name")

    aggregations = {
        "spend": ("spend", "sum"),
        "booked_revenue": ("booked_revenue", "sum"),
        "gross_margin": ("gross_margin", "sum"),
        "impressions": ("impressions", "sum"),
        "clicks": ("clicks", "sum"),
        "leads": ("leads", "sum"),
        "qualified_leads": ("qualified_leads", "sum"),
        "closed_won_conversions": ("closed_won_conversions", "sum"),
    }
    available_aggs = {name: spec for name, spec in aggregations.items() if spec[0] in frame.columns}
    output = frame.groupby(group_cols, dropna=False).agg(**available_aggs).reset_index()
    output["ctr"] = output.apply(lambda row: safe_divide(row.get("clicks", 0), row.get("impressions", 0)), axis=1)
    output["cpc"] = output.apply(lambda row: safe_divide(row.get("spend", 0), row.get("clicks", 0)), axis=1)
    output["cac"] = output.apply(lambda row: safe_divide(row.get("spend", 0), row.get("closed_won_conversions", 0)), axis=1)
    # kpi_catalog_key: roas
    output["roas"] = output.apply(lambda row: safe_divide(row.get("booked_revenue", 0), row.get("spend", 0)), axis=1)
    output["conversion_rate"] = output.apply(
        lambda row: safe_divide(row.get("closed_won_conversions", 0), row.get("leads", 0)),
        axis=1,
    )
    return output.fillna(0)


def _float_value(row: pd.Series | dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in row and pd.notna(row[key]):
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return 0.0


def _bool_value(row: pd.Series | dict[str, Any], key: str) -> bool:
    if key not in row or pd.isna(row[key]):
        return False
    value = row[key]
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _has_any_key(row: pd.Series | dict[str, Any], *keys: str) -> bool:
    return any(key in row for key in keys)
