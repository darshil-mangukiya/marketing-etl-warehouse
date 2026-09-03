from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
ANALYST_DIR = EXPORT_DIR / "analyst_outputs"
REPORT_DIR = PROJECT_ROOT / "reports" / "generated"


def _read(name: str) -> pd.DataFrame:
    path = EXPORT_DIR / f"demo_{name}.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _safe_divide(numerator: pd.Series | float, denominator: pd.Series | float) -> pd.Series | float:
    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        num = pd.to_numeric(numerator, errors="coerce").fillna(0)
        den = pd.to_numeric(denominator, errors="coerce").replace(0, pd.NA)
        return (num / den).fillna(0)
    return float(numerator) / float(denominator) if denominator else 0.0


def campaign_roi_driver_analysis() -> pd.DataFrame:
    campaign = _read("mart_campaign_performance")
    if campaign.empty:
        return campaign
    output = campaign.copy()
    output["campaign_roi"] = _safe_divide(output["attributed_revenue"] - output["spend"], output["spend"])
    output["roi_driver"] = output.apply(
        lambda row: "scale" if row["campaign_roi"] >= 1 else ("investigate_spend" if row["spend"] > output["spend"].median() else "optimize"),
        axis=1,
    )
    return output.sort_values(["campaign_roi", "spend"], ascending=[True, False]).head(50)


def campaign_action_recommendations() -> pd.DataFrame:
    campaign = _read("mart_campaign_performance")
    channel = _read("mart_channel_performance")
    target = _read("mart_target_vs_actual")
    quality = _read("mart_data_quality_monitoring")
    if campaign.empty:
        return pd.DataFrame(
            columns=[
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
            ]
        )

    output = campaign.copy()
    output["channel"] = output.get("normalized_channel", "unknown")
    output["platform"] = output["channel"].map(
        {"paid_search": "google_ads", "paid_social": "facebook_tiktok_ads"}
    ).fillna("multi_source")
    output["region"] = "multi_region"
    output["revenue"] = pd.to_numeric(output.get("attributed_revenue", 0), errors="coerce").fillna(0)
    output["spend"] = pd.to_numeric(output.get("spend", 0), errors="coerce").fillna(0)
    output["roas"] = _safe_divide(output["revenue"], output["spend"])
    output["campaign_roi_pct"] = _safe_divide(output["revenue"] - output["spend"], output["spend"])
    output["conversion_rate"] = _safe_divide(output.get("conversions", 0), output.get("clicks", 0))
    output["attribution_coverage_pct"] = (output["revenue"].gt(0) & pd.to_numeric(output.get("conversions", 0), errors="coerce").fillna(0).gt(0)).astype(float)

    if not channel.empty and "normalized_channel" in channel.columns:
        channel_rollup = (
            channel.groupby("normalized_channel", dropna=False)
            .agg(
                channel_spend=("spend", "sum"),
                channel_conversions=("closed_won_conversions", "sum"),
                channel_leads=("leads", "sum"),
            )
            .reset_index()
        )
        channel_rollup["cac"] = _safe_divide(channel_rollup["channel_spend"], channel_rollup["channel_conversions"])
        channel_rollup["lead_to_customer_rate"] = _safe_divide(
            channel_rollup["channel_conversions"], channel_rollup["channel_leads"]
        )
        output = output.merge(channel_rollup[["normalized_channel", "cac", "lead_to_customer_rate"]], how="left", left_on="channel", right_on="normalized_channel")
        output = output.drop(columns=["normalized_channel_y"], errors="ignore").rename(columns={"normalized_channel_x": "normalized_channel"})
    else:
        output["cac"] = 0.0
        output["lead_to_customer_rate"] = 0.0

    if not target.empty and "channel" in target.columns:
        target_rollup = (
            target.groupby("channel", dropna=False)
            .agg(
                budget_pacing_pct=("spend_attainment", "mean"),
                target_attainment_pct=("revenue_attainment", "mean"),
            )
            .reset_index()
        )
        output = output.merge(target_rollup, how="left", left_on="channel", right_on="channel")
    else:
        output["budget_pacing_pct"] = 0.0
        output["target_attainment_pct"] = 0.0

    quality_flag = "healthy"
    if not quality.empty and "monitoring_status" in quality.columns:
        statuses = set(quality["monitoring_status"].dropna().astype(str).str.lower())
        if any("failure" in status for status in statuses):
            quality_flag = "quality_failure"
        elif any("warning" in status or "risk" in status for status in statuses):
            quality_flag = "quality_warning"
    output["data_quality_flag"] = quality_flag

    median_spend = float(output["spend"].median()) if len(output) else 0.0

    def decide(row: pd.Series) -> tuple[str, str, str]:
        if row["data_quality_flag"] != "healthy":
            return "Fix Data Quality Issue", "P1", "Source-health or validation outputs contain warnings/failures."
        if row["attribution_coverage_pct"] < 0.7 and row.get("conversions", 0) > 0:
            return "Investigate Attribution Gap", "P1", "Conversions exist but attributed revenue coverage is weak."
        if row["roas"] >= 2.0 and row["conversion_rate"] >= 0.02 and row["budget_pacing_pct"] <= 1.10:
            return "Scale", "P2", "ROAS and conversion efficiency are strong without excessive pacing."
        if row["spend"] >= median_spend and row["roas"] < 1.0 and row["conversion_rate"] < 0.02:
            return "Pause", "P0", "High spend combines with weak ROAS and conversion rate."
        if row["target_attainment_pct"] < 0.75 and row["roas"] >= 1.5:
            return "Reallocate Budget", "P1", "Efficient campaign/channel has room to help close target gaps."
        if row["conversion_rate"] < 0.02 and row.get("clicks", 0) > 0:
            return "Improve Funnel Quality", "P2", "Traffic exists but conversion quality is weak."
        return "Monitor", "P3", "Performance is mixed or within expected monitoring range."

    decisions = output.apply(decide, axis=1, result_type="expand")
    output["recommended_action"] = decisions[0]
    output["action_priority"] = decisions[1]
    output["action_reason"] = decisions[2]
    return output[
        [
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
        ]
    ].sort_values(["action_priority", "spend"], ascending=[True, False])


def channel_efficiency_segmentation() -> pd.DataFrame:
    channel = _read("mart_channel_performance")
    if channel.empty:
        return channel
    output = channel.copy()
    output["efficiency_segment"] = pd.cut(
        output["roas"],
        bins=[-1, 0.75, 1.5, 3.0, float("inf")],
        labels=["loss_making", "weak", "healthy", "scale_candidate"],
    ).astype(str)
    return output.sort_values("roas", ascending=False)


def funnel_dropoff_analysis() -> pd.DataFrame:
    funnel = _read("mart_funnel_performance")
    if funnel.empty:
        return funnel
    output = funnel.copy()
    output["mql_dropoff"] = 1 - output["lead_to_mql_rate"]
    output["sql_dropoff"] = 1 - output["mql_to_sql_rate"]
    output["close_dropoff"] = 1 - output["sql_to_close_rate"]
    return output.sort_values(["close_dropoff", "sql_dropoff"], ascending=False)


def conversion_forecasting() -> pd.DataFrame:
    forecast = _read("mart_performance_forecast")
    if forecast.empty:
        return forecast
    output = forecast.copy()
    output["methodology"] = "moving_average_projection_from_demo_marts"
    return output


def campaign_anomaly_detection() -> pd.DataFrame:
    anomalies = _read("mart_marketing_anomalies")
    if anomalies.empty:
        return anomalies
    output = anomalies.copy()
    output["methodology"] = "rule_based_threshold_and_z_score_flags"
    return output


def budget_pacing_alerts() -> pd.DataFrame:
    pacing = _read("mart_budget_pacing")
    if pacing.empty:
        return pacing
    output = pacing.copy()
    output["alert_level"] = output["pacing_status"].map(
        {"over_pacing": "review_now", "under_pacing": "review_now", "on_track": "monitor"}
    ).fillna("monitor")
    return output


def customer_value_analysis() -> pd.DataFrame:
    customer = _read("mart_customer_value")
    if customer.empty:
        return customer
    output = customer.copy()
    output["value_rank"] = output["lifetime_revenue"].rank(method="dense", ascending=False)
    return output.sort_values("lifetime_revenue", ascending=False).head(100)


def executive_insight_generator() -> pd.DataFrame:
    scorecard = _read("mart_executive_scorecard")
    action = _read("mart_action_center")
    insights = []
    if not scorecard.empty:
        row = scorecard.iloc[0]
        insights.append(
            {
                "insight_type": "executive_summary",
                "priority": "P1",
                "finding": str(row.get("board_narrative", "Review executive scorecard.")),
                "recommended_action": "Review channel and campaign ROI drivers before budget reallocation.",
            }
        )
    if not action.empty:
        for item in action.head(10).itertuples(index=False):
            insights.append(
                {
                    "insight_type": "action_center",
                    "priority": getattr(item, "priority", "P2"),
                    "finding": getattr(item, "title", "Operational action"),
                    "recommended_action": getattr(item, "recommended_action", "Review in dashboard."),
                }
            )
    return pd.DataFrame(insights)


def executive_insights() -> pd.DataFrame:
    channel = _read("mart_channel_performance")
    campaign = _read("mart_campaign_performance")
    funnel = _read("mart_funnel_performance")
    target = _read("mart_target_vs_actual")
    attribution = _read("mart_attribution_model_comparison")
    customer = _read("mart_customer_segment_mix")
    quality = _read("mart_data_quality_monitoring")
    actions = campaign_action_recommendations()
    rows: list[dict[str, object]] = []

    def add(category: str, title: str, detail: str, metric: object, action: str, priority: str) -> None:
        rows.append(
            {
                "insight_id": f"INS-{len(rows) + 1:03d}",
                "insight_category": category,
                "insight_title": title,
                "insight_detail": detail,
                "evidence_metric": metric,
                "recommended_action": action,
                "priority": priority,
            }
        )

    if not channel.empty:
        best = channel.sort_values("roas", ascending=False).iloc[0]
        worst = channel.sort_values("roas", ascending=True).iloc[0]
        add(
            "channel efficiency",
            f"{best.get('channel_name', best.get('normalized_channel', 'A channel'))} leads channel efficiency",
            f"Highest observed channel ROAS is {float(best.get('roas', 0)):.2f}x; weakest channel ROAS is {float(worst.get('roas', 0)):.2f}x.",
            f"best_roas={float(best.get('roas', 0)):.2f}",
            "Review budget shift from weak to efficient channels.",
            "P1",
        )
    if not campaign.empty:
        risky = campaign[(campaign["spend"] > campaign["spend"].median()) & (campaign["attributed_roas"] < 1)]
        add(
            "campaign ROI",
            "High-spend low-return campaigns need review",
            f"{len(risky)} campaigns spend above the median while attributed ROAS is below 1.0x.",
            f"campaign_count={len(risky)}",
            "Use the campaign action recommendation output to decide pause, monitor, or reallocation.",
            "P0" if len(risky) else "P2",
        )
    if not funnel.empty:
        close_row = funnel.sort_values("sql_to_close_rate", ascending=True).iloc[0]
        add(
            "funnel drop-off",
            "SQL-to-close is the funnel stage to inspect",
            f"Weakest SQL-to-close rate is {float(close_row.get('sql_to_close_rate', 0)):.1%}.",
            f"sql_to_close_rate={float(close_row.get('sql_to_close_rate', 0)):.4f}",
            "Review sales handoff and lead quality for low-close segments.",
            "P1",
        )
    if not target.empty:
        avg_revenue_attainment = float(pd.to_numeric(target.get("revenue_attainment", 0), errors="coerce").fillna(0).mean())
        avg_spend_attainment = float(pd.to_numeric(target.get("spend_attainment", 0), errors="coerce").fillna(0).mean())
        add(
            "target attainment",
            "Target attainment is below plan",
            f"Average revenue attainment is {avg_revenue_attainment:.1%}; average spend attainment is {avg_spend_attainment:.1%}.",
            f"revenue_attainment={avg_revenue_attainment:.4f}",
            "Separate budget under-pacing from performance under-delivery before reallocating spend.",
            "P1",
        )
    if not attribution.empty:
        delta_cols = [column for column in attribution.columns if "delta" in column]
        delta_value = float(pd.to_numeric(attribution[delta_cols].abs().sum(axis=1), errors="coerce").fillna(0).max()) if delta_cols else 0.0
        add(
            "attribution differences",
            "Attribution model choice changes ROI interpretation",
            "Attribution comparison marts show variance between model outputs.",
            f"max_model_delta={delta_value:.2f}",
            "Use attribution page notes when presenting campaign ROI to stakeholders.",
            "P2",
        )
    if not customer.empty:
        top_segment = customer.sort_values("lifetime_revenue", ascending=False).iloc[0] if "lifetime_revenue" in customer.columns else customer.iloc[0]
        add(
            "customer value",
            "Customer value segmentation is ready for channel analysis",
            f"Top customer segment in the demo mart is {top_segment.get('customer_segment', 'unknown')}.",
            top_segment.get("customer_segment", "unknown"),
            "Connect campaign/channel acquisition paths to value segments before scaling.",
            "P2",
        )
    if not quality.empty:
        rejected = int(pd.to_numeric(quality.get("rejected_count", 0), errors="coerce").fillna(0).sum())
        add(
            "source/data quality",
            "Data-quality caveats should stay visible",
            f"Validation outputs include {rejected} rejected rows in the current demo evidence.",
            f"rejected_rows={rejected}",
            "Keep quality badges and source-health views in executive reporting.",
            "P1" if rejected else "P3",
        )
    if not actions.empty:
        top_actions = actions["recommended_action"].value_counts().head(3).to_dict()
        add(
            "recommended next actions",
            "Campaign action queue is available",
            f"Top recommendation mix: {top_actions}.",
            top_actions,
            "Review P0/P1 recommendations first, then validate with channel/funnel pages.",
            "P1",
        )
    return pd.DataFrame(rows)


REPORTS = {
    "campaign_roi_driver_analysis": campaign_roi_driver_analysis,
    "campaign_action_recommendations": campaign_action_recommendations,
    "channel_efficiency_segmentation": channel_efficiency_segmentation,
    "funnel_dropoff_analysis": funnel_dropoff_analysis,
    "conversion_forecasting": conversion_forecasting,
    "campaign_anomaly_detection": campaign_anomaly_detection,
    "budget_pacing_alerts": budget_pacing_alerts,
    "customer_value_analysis": customer_value_analysis,
    "executive_insight_generator": executive_insight_generator,
    "executive_insights": executive_insights,
}


def _write_campaign_action_report(frame: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actions = frame["recommended_action"].value_counts().to_dict() if not frame.empty else {}
    text = f"""# Campaign Action Recommendations

## Business Purpose

This output translates campaign ROI, spend, conversion, target, attribution, and data-quality signals into deterministic campaign recommendations. It is designed for analyst review and stakeholder discussion, not automated budget execution.

## Fields

Key fields include campaign ID/name, channel, platform, spend, attributed revenue, ROAS, campaign ROI %, CAC, conversion rate, lead-to-customer rate, budget pacing %, target attainment %, attribution coverage %, data-quality flag, recommended action, action priority, and action reason.

## Scoring Logic

- **Scale**: strong ROAS, healthy conversion rate, and budget pacing not excessive.
- **Pause**: high spend, weak ROAS, and weak conversion rate.
- **Reallocate Budget**: target attainment is low while performance is efficient.
- **Improve Funnel Quality**: traffic exists but conversion quality is weak.
- **Investigate Attribution Gap**: conversions exist but attribution coverage is weak.
- **Fix Data Quality Issue**: validation or source-health flags are present.
- **Monitor**: mixed performance or no urgent signal.

## Current Recommendation Mix

{actions}

## Review Scope

The logic uses generated local marts and deterministic thresholds. Analyst review remains part of the operating pattern before budget changes.
"""
    (PROJECT_ROOT / "reports" / "campaign_action_recommendations.md").write_text(text, encoding="utf-8")


def _write_executive_insights_report(frame: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if frame.empty:
        body = "No executive insights were generated because required demo marts were missing."
    else:
        top = "\n".join(
            f"- **{row.insight_title}** ({row.priority}): {row.insight_detail} Recommended action: {row.recommended_action}"
            for row in frame.head(5).itertuples(index=False)
        )
        risks = "\n".join(
            f"- {row.insight_title}: {row.insight_detail}"
            for row in frame[frame["priority"].isin(["P0", "P1"])].head(5).itertuples(index=False)
        )
        body = f"""## Executive Summary

The generated insights summarize channel efficiency, campaign ROI, high-spend low-return risk, funnel drop-off, budget pacing, target attainment, attribution differences, customer value, source/data quality, and recommended next actions.

## Top 5 Insights

{top}

## Risks To Review

{risks or "- No P0/P1 insights were generated."}

## Opportunities To Scale

- Review campaigns marked `Scale` in `data/exports/analyst_outputs/campaign_action_recommendations.csv`.
- Compare channel ROAS and CAC before moving budget.

## Data-Quality Caveats

- Generated project data keeps the workflow reproducible without customer records.
- Recommendations are designed as analyst decision support; budget automation is a deployment extension.

## Recommended 30/60/90-Day Actions

- 30 days: validate campaign action logic with stakeholders and confirm KPI definitions.
- 60 days: review the committed Power BI Desktop report and refresh screenshots after model changes.
- 90 days: extend the pattern with managed API connectors or cloud warehouse deployment when needed.
"""
    (PROJECT_ROOT / "reports" / "executive_insights_summary.md").write_text("# Executive Insights Summary\n\n" + body.strip() + "\n", encoding="utf-8")


def generate_all() -> dict:
    ANALYST_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "outputs": []}
    for name, builder in REPORTS.items():
        frame = builder()
        output_name = "executive_insights" if name == "executive_insights" else name
        output_path = ANALYST_DIR / f"{output_name}.csv"
        frame.to_csv(output_path, index=False)
        manifest["outputs"].append({"name": name, "row_count": len(frame), "file": str(output_path.relative_to(PROJECT_ROOT))})
        if name == "campaign_action_recommendations":
            _write_campaign_action_report(frame)
        if name == "executive_insights":
            _write_executive_insights_report(frame)
    summary = pd.DataFrame(manifest["outputs"])
    summary_path = REPORT_DIR / "analyst_output_manifest.csv"
    summary.to_csv(summary_path, index=False)
    manifest["manifest_file"] = str(summary_path.relative_to(PROJECT_ROOT))
    (ANALYST_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main_for_report(report_name: str) -> None:
    if report_name not in REPORTS:
        raise SystemExit(f"Unknown report: {report_name}")
    ANALYST_DIR.mkdir(parents=True, exist_ok=True)
    frame = REPORTS[report_name]()
    output_name = "executive_insights" if report_name == "executive_insights" else report_name
    output_path = ANALYST_DIR / f"{output_name}.csv"
    frame.to_csv(output_path, index=False)
    if report_name == "campaign_action_recommendations":
        _write_campaign_action_report(frame)
    if report_name == "executive_insights":
        _write_executive_insights_report(frame)
    print(json.dumps({"report": report_name, "row_count": len(frame), "file": str(output_path.relative_to(PROJECT_ROOT))}, indent=2))


def main() -> None:
    print(json.dumps(generate_all(), indent=2))


if __name__ == "__main__":
    main()
