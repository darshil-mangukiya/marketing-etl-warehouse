from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bi_app.charts import bar_chart, funnel_chart, line_chart, scatter_chart
from bi_app.data_loader import (
    DATASET_SPECS,
    apply_date_filter,
    apply_text_search,
    apply_value_filter,
    available_values,
    load_dashboard_datasets,
    source_note,
)
from bi_app.kpi_catalog import kpi_formula, load_kpi_catalog
from bi_app.metrics import (
    add_campaign_recommendations,
    channel_rollup,
    count_rows,
    executive_kpis,
    fmt_money,
    fmt_number,
    fmt_percent,
    fmt_ratio,
    safe_divide,
    sum_column,
)


st.set_page_config(
    page_title="Campaign ROI Reporting Platform",
    page_icon="M",
    layout="wide",
)


DATE_COLUMNS = ("reporting_month", "target_month", "snapshot_month")


def main() -> None:
    apply_theme()
    data = load_dashboard_datasets()
    filters = render_sidebar(data)
    filtered = apply_dashboard_filters(data, filters)

    st.title("Campaign ROI Reporting Automation & Marketing Performance Analytics Platform")
    st.caption(
        "Local analytics environment for campaign ROI, ROAS, CAC, attribution, funnel conversion, "
        "budget pacing, target attainment, and reporting trust."
    )
    st.caption(
        "Privacy-safe project data keeps the local BI workflow reproducible while preserving realistic "
        "campaign, funnel, attribution, target, and data-quality review patterns."
    )
    show_dataset_status(data)

    tabs = st.tabs(
        [
            "Executive Overview",
            "Channel Performance",
            "Campaign Intelligence",
            "Funnel Analysis",
            "Attribution and ROI",
            "Target vs Actual",
            "Data Quality and Monitoring",
            "Customer Value",
            "Source Health",
        ]
    )

    with tabs[0]:
        executive_overview(filtered)
    with tabs[1]:
        channel_performance(filtered)
    with tabs[2]:
        campaign_intelligence(filtered)
    with tabs[3]:
        funnel_analysis(filtered)
    with tabs[4]:
        attribution_and_roi(filtered)
    with tabs[5]:
        target_vs_actual(filtered)
    with tabs[6]:
        data_quality_monitoring(filtered)
    with tabs[7]:
        customer_value(filtered)
    with tabs[8]:
        source_health(filtered)


def render_sidebar(data: dict[str, pd.DataFrame]) -> dict[str, object]:
    with st.sidebar:
        st.header("Filters")
        role_view = st.radio(
            "Role view",
            ["Analyst View", "BA View", "BI Developer View"],
            horizontal=False,
        )
        render_role_note(role_view)
        date_range = date_filter(data.values())

        channels = available_values(
            [
                data["channel_performance"],
                data["campaign_performance"],
                data["funnel_performance"],
                data["target_vs_actual"],
                data["budget_pacing"],
                data["journey_quality"],
            ],
            ("normalized_channel", "channel"),
        )
        selected_channels = st.multiselect("Channel", channels, default=channels)

        campaign_search = st.text_input("Campaign contains")

        regions = available_values([data["target_vs_actual"]], ("region",))
        selected_regions = st.multiselect("Region", regions, default=regions) if regions else []

        devices = available_values([data["device_performance"]], ("device",))
        selected_devices = st.multiselect("Device", devices, default=devices) if devices else []

        sources = available_values(
            [data["data_quality_monitoring"], data["source_health"]],
            ("source_system",),
        )
        selected_sources = st.multiselect("Source system", sources, default=sources) if sources else []

        st.divider()
        st.download_button(
            "Download channel mart",
            data["channel_performance"].to_csv(index=False).encode("utf-8"),
            file_name="mart_channel_performance.csv",
            mime="text/csv",
            disabled=data["channel_performance"].empty,
        )

    return {
        "role_view": role_view,
        "date_range": date_range,
        "channels": selected_channels,
        "campaign_search": campaign_search,
        "regions": selected_regions,
        "devices": selected_devices,
        "sources": selected_sources,
    }


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f8fafc; color: #0f172a; }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 10px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #dbe3ef; }
        h1, h2, h3 { color: #0f2742; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 8px 8px 0 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_role_note(role_view: str) -> None:
    notes = {
        "Analyst View": "Focus: ROI drivers, high-spend/low-return campaigns, funnel leakage, attribution differences.",
        "BA View": "Focus: stakeholder questions, KPI definitions, UAT evidence, and decision workflows.",
        "BI Developer View": "Focus: semantic tables, relationship grain, DAX definitions, refresh and quality controls.",
    }
    st.info(notes[role_view])
    catalog = load_kpi_catalog()
    st.caption(f"Governed KPI keys loaded: {len(catalog.get('kpis', {}))}")


def date_filter(frames: Iterable[pd.DataFrame]) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    dates: list[pd.Timestamp] = []
    for frame in frames:
        if frame.empty:
            continue
        for column in DATE_COLUMNS:
            if column in frame.columns:
                values = frame[column].dropna()
                if not values.empty:
                    dates.extend([values.min(), values.max()])
    if not dates:
        return None

    min_date = min(dates).date()
    max_date = max(dates).date()
    selected = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected, tuple) and len(selected) == 2:
        return pd.Timestamp(selected[0]), pd.Timestamp(selected[1])
    return pd.Timestamp(min_date), pd.Timestamp(max_date)


def apply_dashboard_filters(data: dict[str, pd.DataFrame], filters: dict[str, object]) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}
    for key, frame in data.items():
        view = apply_date_filter(frame, filters["date_range"])
        view = apply_value_filter(view, filters["channels"], ("normalized_channel", "channel"))
        view = apply_value_filter(view, filters["regions"], ("region",))
        view = apply_value_filter(view, filters["devices"], ("device",))
        view = apply_value_filter(view, filters["sources"], ("source_system",))
        if key in {"campaign_performance", "campaign_optimization"}:
            view = apply_text_search(view, str(filters["campaign_search"]), ("campaign_name", "campaign_id"))
        output[key] = view
    return output


def show_dataset_status(data: dict[str, pd.DataFrame]) -> None:
    missing_required = [
        spec.label for key, spec in DATASET_SPECS.items() if spec.required and data.get(key, pd.DataFrame()).empty
    ]
    if missing_required:
        st.warning(
            "Required dashboard inputs are missing. Run `python3 -B scripts/build_demo_marts.py` "
            f"and refresh the app. Missing: {', '.join(missing_required)}."
        )

    with st.expander("Loaded dashboard inputs", expanded=False):
        status = pd.DataFrame(
            [
                {
                    "dataset": spec.label,
                    "rows": count_rows(data[key]),
                    "source": Path(str(data[key].attrs.get("source_path", "missing"))).name.removeprefix("demo_"),
                    "required": spec.required,
                }
                for key, spec in DATASET_SPECS.items()
            ]
        )
        st.dataframe(status, width="stretch", hide_index=True)


def page_intro(title: str, question: str, *frames: pd.DataFrame) -> None:
    st.subheader(title)
    st.caption(f"Business question: {question}")
    notes = " | ".join(source_note(frame) for frame in frames if frame is not None)
    if notes:
        st.caption(f"Source marts: {notes}")


def render_metrics(items: list[tuple[str, str]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items, strict=False):
        column.metric(label, value)


def executive_overview(data: dict[str, pd.DataFrame]) -> None:
    channel = data["channel_performance"]
    target = data["target_vs_actual"]
    quality = data["data_quality_monitoring"]
    source = data["source_health"]
    funnel = data["funnel_performance"]

    page_intro(
        "Executive Overview",
        "Is marketing performance on track across spend, revenue, ROAS, CAC, conversions, and data quality?",
        channel,
        target,
        quality,
    )

    kpis = executive_kpis(channel, target, quality, source)
    st.caption(f"ROAS formula from KPI catalog: `{kpi_formula('roas')}`")
    render_metrics(
        [
            ("Total Spend", fmt_money(kpis["total_spend"])),
            ("Booked Revenue", fmt_money(kpis["total_revenue"])),
            ("ROAS", fmt_ratio(kpis["roas"])),
            ("CAC", fmt_money(kpis["cac"])),
        ]
    )
    render_metrics(
        [
            ("Leads", fmt_number(kpis["leads"])),
            ("Conversions", fmt_number(kpis["conversions"])),
            ("Target Attainment", fmt_percent(kpis["target_attainment"])),
            ("Data Quality Status", str(kpis["data_quality_status"])),
        ]
    )

    monthly = aggregate_monthly(channel)
    rollup = channel_rollup(channel)
    funnel_summary = build_funnel_summary(funnel)
    target_summary = build_target_summary(data["budget_pacing"], target)
    quality_status = status_counts(quality, "monitoring_status", "count")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            line_chart(monthly, "reporting_month", ["spend", "booked_revenue"], "Spend and Revenue Trend"),
            width="stretch",
            key="executive_spend_revenue_trend",
        )
        st.plotly_chart(
            funnel_chart(funnel_summary, "stage", "count", "Conversion Funnel Summary"),
            width="stretch",
            key="executive_conversion_funnel",
        )
    with right:
        st.plotly_chart(
            bar_chart(rollup, "normalized_channel", "roas", "ROAS by Channel"),
            width="stretch",
            key="executive_roas_by_channel",
        )
        st.plotly_chart(
            bar_chart(target_summary, "metric", "value", "Target vs Actual Summary", color="metric"),
            width="stretch",
            key="executive_target_summary",
        )

    st.plotly_chart(
        bar_chart(quality_status, "monitoring_status", "count", "Data Quality Status Summary", color="monitoring_status"),
        width="stretch",
        key="executive_quality_summary",
    )


def channel_performance(data: dict[str, pd.DataFrame]) -> None:
    channel = data["channel_performance"]
    page_intro("Channel Performance", "Which channels deserve more or less budget?", channel)

    rollup = channel_rollup(channel)
    render_metrics(
        [
            ("Spend", fmt_money(sum_column(rollup, "spend"))),
            ("Revenue", fmt_money(sum_column(rollup, "booked_revenue"))),
            ("ROAS", fmt_ratio(safe_divide(sum_column(rollup, "booked_revenue"), sum_column(rollup, "spend")))),
            (
                "CAC",
                fmt_money(safe_divide(sum_column(rollup, "spend"), sum_column(rollup, "closed_won_conversions"))),
            ),
        ]
    )
    render_metrics(
        [
            ("CPC", fmt_money(safe_divide(sum_column(rollup, "spend"), sum_column(rollup, "clicks")))),
            ("CTR", fmt_percent(safe_divide(sum_column(rollup, "clicks"), sum_column(rollup, "impressions")))),
            ("Leads", fmt_number(sum_column(rollup, "leads"))),
            ("Conversions", fmt_number(sum_column(rollup, "closed_won_conversions"))),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(rollup, "normalized_channel", ["spend", "booked_revenue"], "Spend vs Revenue by Channel"),
            width="stretch",
            key="channel_spend_vs_revenue",
        )
        st.plotly_chart(
            bar_chart(rollup, "normalized_channel", "cac", "CAC by Channel"),
            width="stretch",
            key="channel_cac",
        )
    with right:
        st.plotly_chart(
            bar_chart(rollup, "normalized_channel", "roas", "ROAS by Channel"),
            width="stretch",
            key="channel_roas",
        )
        st.plotly_chart(
            bar_chart(rollup, "normalized_channel", "conversion_rate", "Conversion Rate by Channel"),
            width="stretch",
            key="channel_conversion_rate",
        )

    trend = aggregate_monthly(channel, ["reporting_month", "normalized_channel"])
    st.plotly_chart(
        line_chart(trend, "reporting_month", "booked_revenue", "Revenue Trend by Channel", color="normalized_channel"),
        width="stretch",
        key="channel_revenue_trend",
    )
    st.dataframe(sort_if_possible(rollup, ["roas", "booked_revenue"]), width="stretch", hide_index=True)


def campaign_intelligence(data: dict[str, pd.DataFrame]) -> None:
    campaign = add_campaign_recommendations(data["campaign_performance"])
    optimization = data["campaign_optimization"]
    page_intro("Campaign Intelligence", "Which campaigns should be scaled, optimized, or paused?", campaign, optimization)

    roas_col = "attributed_roas" if "attributed_roas" in campaign.columns else "roas"
    high_roi = int((campaign.get(roas_col, pd.Series(dtype=float)) >= 2).sum()) if not campaign.empty else 0
    low_roi = int((campaign.get(roas_col, pd.Series(dtype=float)) < 1).sum()) if not campaign.empty else 0
    missing_attr = (
        int(campaign["data_quality_flags"].str.contains("missing_attribution", na=False).sum())
        if "data_quality_flags" in campaign.columns
        else 0
    )

    render_metrics(
        [
            ("Campaign Count", fmt_number(count_rows(campaign))),
            ("High ROI Campaigns", fmt_number(high_roi)),
            ("Low ROI Campaigns", fmt_number(low_roi)),
            ("Wasted Spend Flags", fmt_number(sum_column(campaign, "waste_budget_flag"))),
            ("Missing Attribution Flags", fmt_number(missing_attr)),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(
                sort_if_possible(campaign, ["attributed_revenue"]).tail(20),
                "attributed_revenue",
                "campaign_name",
                "Top Campaigns by Revenue",
                color="recommendation_label",
                orientation="h",
            ),
            width="stretch",
            key="campaign_top_revenue",
        )
        st.plotly_chart(
            scatter_chart(
                campaign,
                "spend",
                "conversions",
                "Spend vs Conversions",
                color="recommendation_label",
                size="attributed_revenue",
                hover_data=["campaign_id", "campaign_name", roas_col],
            ),
            width="stretch",
            key="campaign_spend_vs_conversions",
        )
    with right:
        bottom_roi = campaign[campaign.get("spend", pd.Series(dtype=float)) > 0] if not campaign.empty else campaign
        st.plotly_chart(
            bar_chart(
                sort_if_possible(bottom_roi, [roas_col]).head(20),
                roas_col,
                "campaign_name",
                "Bottom Campaigns by ROI",
                color="recommendation_label",
                orientation="h",
            ),
            width="stretch",
            key="campaign_bottom_roi",
        )
        rec_counts = status_counts(campaign, "recommendation_label", "campaigns")
        st.plotly_chart(
            bar_chart(rec_counts, "recommendation_label", "campaigns", "Recommendation Label Summary", color="recommendation_label"),
            width="stretch",
            key="campaign_recommendation_summary",
        )

    with st.expander("Recommendation rule"):
        example = {
            "Scale": "ROAS >= 2.0 and at least 10 conversions.",
            "Monitor": "Campaign is not clearly strong or weak under the simple thresholds.",
            "Optimize": "ROAS below 1.25 or conversions exist without attributed revenue.",
            "Pause Candidate": "Waste flag is true, or spend is above the campaign median while ROAS is below 0.75.",
        }
        st.json(example)

    columns = [
        column
        for column in [
            "campaign_id",
            "campaign_name",
            "normalized_channel",
            "spend",
            "conversions",
            "attributed_revenue",
            roas_col,
            "recommendation_label",
            "data_quality_flags",
        ]
        if column in campaign.columns
    ]
    st.dataframe(sort_if_possible(campaign[columns], ["recommendation_label", "spend"]), width="stretch", hide_index=True)


def funnel_analysis(data: dict[str, pd.DataFrame]) -> None:
    funnel = data["funnel_performance"]
    journey = data["journey_quality"]
    conversion_lag = data["conversion_lag"]
    page_intro("Funnel Analysis", "Where are leads dropping off?", funnel, journey, conversion_lag)

    sessions = sum_column(journey, "sessions")
    leads = sum_column(funnel, "total_leads") or sum_column(journey, "leads")
    mqls = sum_column(funnel, "mqls")
    sqls = sum_column(funnel, "sales_qualified_leads")
    conversions = sum_column(funnel, "conversions") or sum_column(journey, "conversions")

    render_metrics(
        [
            ("Sessions", fmt_number(sessions)),
            ("Leads", fmt_number(leads)),
            ("MQLs", fmt_number(mqls)),
            ("SQLs", fmt_number(sqls)),
            ("Conversions", fmt_number(conversions)),
            ("Lead Conversion Rate", fmt_percent(safe_divide(leads, sessions))),
            ("Closed-Won Rate", fmt_percent(safe_divide(conversions, sqls))),
        ]
    )

    stage_summary = build_stage_summary(leads, mqls, sqls, conversions)
    rate_summary = build_rate_summary(funnel)
    by_channel = build_funnel_by_channel(funnel)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            funnel_chart(stage_summary, "stage", "count", "Funnel Stage Volume"),
            width="stretch",
            key="funnel_stage_volume",
        )
        st.plotly_chart(
            bar_chart(rate_summary, "rate", "value", "Stage Conversion Rates"),
            width="stretch",
            key="funnel_stage_rates",
        )
    with right:
        st.plotly_chart(
            bar_chart(by_channel, "normalized_channel", "conversions", "Funnel Conversions by Channel", color="normalized_channel"),
            width="stretch",
            key="funnel_conversions_by_channel",
        )
        st.plotly_chart(
            bar_chart(conversion_lag, "conversion_lag_bucket", "conversions", "Lead-to-Conversion Lag", color="product"),
            width="stretch",
            key="funnel_conversion_lag",
        )

    st.dataframe(funnel, width="stretch", hide_index=True)


def attribution_and_roi(data: dict[str, pd.DataFrame]) -> None:
    attribution = data["attribution_summary"]
    comparison = data["attribution_model_comparison"]
    reconciliation = data["attribution_reconciliation"]
    journey = data["journey_quality"]
    conversion_lag = data["conversion_lag"]
    page_intro(
        "Attribution and ROI",
        "How do attribution gaps affect ROI reporting?",
        attribution,
        comparison,
        reconciliation,
    )
    st.info("Attribution results use generated project data and simplified attribution logic.")

    missing_conversions = sum_column(journey, "conversions_missing_attribution")
    total_conversions = sum_column(journey, "conversions")
    avg_lag = weighted_average(conversion_lag, "avg_conversion_lag_days", "conversions")

    render_metrics(
        [
            ("Attributed Revenue", fmt_money(sum_column(attribution, "attributed_revenue"))),
            ("Unattributed Conversions", fmt_number(missing_conversions)),
            ("Missing Attribution ID Rate", fmt_percent(safe_divide(missing_conversions, total_conversions))),
            ("First Touch Revenue", fmt_money(sum_column(comparison, "first_touch_revenue"))),
            ("Last Touch Revenue", fmt_money(sum_column(comparison, "last_touch_revenue"))),
            ("Avg Conversion Lag", f"{avg_lag:.1f} days"),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(attribution, "attribution_model", "attributed_revenue", "Revenue by Attribution Model", color="attribution_model"),
            width="stretch",
            key="attribution_revenue_by_model",
        )
        coverage = journey[["normalized_channel", "attribution_coverage"]] if _has_columns(journey, ["normalized_channel", "attribution_coverage"]) else pd.DataFrame()
        st.plotly_chart(
            bar_chart(coverage, "normalized_channel", "attribution_coverage", "Attribution Coverage by Channel"),
            width="stretch",
            key="attribution_coverage_by_channel",
        )
    with right:
        st.plotly_chart(
            line_chart(
                comparison,
                "reporting_month",
                [
                    "first_touch_revenue",
                    "last_touch_revenue",
                    "linear_revenue",
                    "time_decay_revenue",
                    "u_shaped_revenue",
                ],
                "Attribution Model Comparison",
            ),
            width="stretch",
            key="attribution_model_comparison",
        )
        missing = build_missing_attribution_summary(journey)
        st.plotly_chart(
            bar_chart(missing, "normalized_channel", "missing_attribution_records", "Missing Attribution by Channel"),
            width="stretch",
            key="attribution_missing_by_channel",
        )

    st.dataframe(attribution, width="stretch", hide_index=True)
    if not reconciliation.empty:
        st.dataframe(reconciliation, width="stretch", hide_index=True)


def target_vs_actual(data: dict[str, pd.DataFrame]) -> None:
    target = data["target_vs_actual"]
    pacing = data["budget_pacing"]
    page_intro(
        "Target vs Actual",
        "Are campaigns, channels, and regions meeting budget and performance targets?",
        target,
        pacing,
    )

    target_spend = sum_column(pacing, "target_spend") or sum_column(target, "target_spend")
    actual_spend = sum_column(pacing, "actual_spend") or sum_column(target, "actual_spend")
    target_revenue = sum_column(pacing, "target_revenue") or sum_column(target, "target_revenue")
    actual_revenue = sum_column(pacing, "actual_revenue") or sum_column(target, "actual_revenue")
    budget_variance = actual_spend - target_spend
    target_attainment = safe_divide(actual_revenue, target_revenue)
    pacing_status = most_common_value(pacing, "pacing_status")

    render_metrics(
        [
            ("Spend Target", fmt_money(target_spend)),
            ("Actual Spend", fmt_money(actual_spend)),
            ("Budget Variance", fmt_money(budget_variance)),
            ("Revenue Target", fmt_money(target_revenue)),
            ("Actual Revenue", fmt_money(actual_revenue)),
            ("Target Attainment", fmt_percent(target_attainment)),
            ("Pacing Status", pacing_status),
        ]
    )

    monthly = build_target_monthly(pacing if not pacing.empty else target)
    channel_attainment = build_channel_attainment(pacing if not pacing.empty else target)
    region_variance = build_region_variance(target)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(monthly, "target_month", ["target_revenue", "actual_revenue"], "Revenue Target vs Actual by Month"),
            width="stretch",
            key="target_revenue_monthly",
        )
        st.plotly_chart(
            bar_chart(region_variance, "region", "budget_variance", "Budget Variance by Region"),
            width="stretch",
            key="target_budget_variance_region",
        )
    with right:
        st.plotly_chart(
            bar_chart(channel_attainment, "channel", "revenue_attainment", "Target Attainment by Channel", color="pacing_status"),
            width="stretch",
            key="target_attainment_channel",
        )
        status = status_counts(pacing, "pacing_status", "rows")
        st.plotly_chart(
            bar_chart(status, "pacing_status", "rows", "Pacing Status", color="pacing_status"),
            width="stretch",
            key="target_pacing_status",
        )

    st.dataframe(pacing if not pacing.empty else target, width="stretch", hide_index=True)


def data_quality_monitoring(data: dict[str, pd.DataFrame]) -> None:
    quality = data["data_quality_monitoring"]
    source = data["source_health"]
    journey = data["journey_quality"]
    page_intro(
        "Data Quality and Monitoring",
        "Can users trust today's dashboard?",
        quality,
        source,
        journey,
    )

    issue_details = build_quality_issue_details(quality, source, journey)
    source_status = most_common_value(source, "source_health_status")
    latest_pipeline_status = "Passed" if not issue_details["severity"].eq("critical").any() else "Needs Review"

    render_metrics(
        [
            ("Source Freshness Status", source_status),
            ("Rejected Records", fmt_number(sum_column(quality, "rejected_count") or sum_column(source, "rejected"))),
            ("Quality Failures", fmt_number(sum_column(quality, "issue_count") + sum_column(source, "quality_issue_count"))),
            ("Schema Drift Flags", fmt_number(sum_column(quality, "schema_drift_flags"))),
        ]
    )
    render_metrics(
        [
            ("Missing Attribution IDs", fmt_number(sum_column(journey, "leads_missing_attribution") + sum_column(journey, "conversions_missing_attribution"))),
            ("Null Spend Records", fmt_number(sum_column(quality, "null_spend_records"))),
            ("Orphan Conversions", fmt_number(sum_column(journey, "orphan_conversions"))),
            ("Latest Pipeline Status", latest_pipeline_status),
        ]
    )

    left, right = st.columns(2)
    with left:
        failures = issue_details.groupby(["issue_type", "severity"], dropna=False).agg(count=("count", "sum")).reset_index()
        st.plotly_chart(
            bar_chart(failures, "issue_type", "count", "Quality Failures by Type", color="severity"),
            width="stretch",
            key="quality_failures_by_type",
        )
        st.plotly_chart(
            bar_chart(quality, "source_system", "rejected_count", "Rejected Records by Source", color="monitoring_status"),
            width="stretch",
            key="quality_rejected_by_source",
        )
    with right:
        source_counts = status_counts(source, "source_health_status", "sources")
        st.plotly_chart(
            bar_chart(source_counts, "source_health_status", "sources", "Source Freshness and Health Status", color="source_health_status"),
            width="stretch",
            key="quality_source_health",
        )
        status = status_counts(quality, "monitoring_status", "files")
        st.plotly_chart(
            bar_chart(status, "monitoring_status", "files", "Pipeline Quality Run Summary", color="monitoring_status"),
            width="stretch",
            key="quality_pipeline_summary",
        )

    st.caption("References: `docs/data_quality_framework.md` and `local_ci/latest_quality_gate.json`.")
    st.dataframe(issue_details, width="stretch", hide_index=True)
    st.dataframe(quality, width="stretch", hide_index=True)


def customer_value(data: dict[str, pd.DataFrame]) -> None:
    customer = data["customer_value"]
    segment = data["customer_segment_mix"]
    page_intro("Customer Value", "Which customer segments and channels produce higher-value customers?", customer, segment)

    render_metrics(
        [
            ("Customers", fmt_number(customer["customer_id"].nunique() if "customer_id" in customer.columns else sum_column(segment, "customers"))),
            ("Lifetime Revenue", fmt_money(sum_column(customer, "lifetime_revenue") or sum_column(segment, "lifetime_revenue"))),
            ("Lifetime Margin", fmt_money(sum_column(customer, "lifetime_margin") or sum_column(segment, "lifetime_margin"))),
            (
                "Avg Revenue / Customer",
                fmt_money(
                    safe_divide(
                        sum_column(customer, "lifetime_revenue") or sum_column(segment, "lifetime_revenue"),
                        count_rows(customer) or sum_column(segment, "customers"),
                    )
                ),
            ),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(segment, "customer_segment", ["lifetime_revenue", "lifetime_margin"], "Customer Segment Value"),
            width="stretch",
            key="customer_segment_value",
        )
    with right:
        st.plotly_chart(
            bar_chart(segment, "customer_segment", "margin_rate", "Margin Rate by Segment", color="segment_priority"),
            width="stretch",
            key="customer_margin_rate",
        )
    st.dataframe(sort_if_possible(segment, ["lifetime_revenue"]), width="stretch", hide_index=True)
    if not customer.empty:
        st.dataframe(sort_if_possible(customer, ["lifetime_revenue"]).tail(100), width="stretch", hide_index=True)


def source_health(data: dict[str, pd.DataFrame]) -> None:
    source = data["source_health"]
    page_intro("Source Health", "Which source systems need engineering or data-quality attention?", source)

    render_metrics(
        [
            ("Sources", fmt_number(count_rows(source))),
            ("Accepted Records", fmt_number(sum_column(source, "accepted"))),
            ("Rejected Records", fmt_number(sum_column(source, "rejected"))),
            ("Healthy Sources", fmt_number((source.get("source_health_status", pd.Series(dtype=str)) == "healthy").sum())),
            ("Attention Sources", fmt_number((source.get("source_health_status", pd.Series(dtype=str)) != "healthy").sum())),
        ]
    )

    source_melt = melt_existing(
        source,
        id_vars=["source_system", "source_health_status"],
        value_vars=["accepted", "rejected", "failed", "skipped"],
        var_name="record_status",
        value_name="records",
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(source_melt, "source_system", "records", "Accepted, Rejected, Failed, and Skipped Records", color="record_status"),
            width="stretch",
            key="source_record_status",
        )
    with right:
        st.plotly_chart(
            scatter_chart(
                source,
                "acceptance_rate",
                "quality_issue_count",
                "Acceptance Rate vs Quality Issues",
                color="source_health_status",
                size="rows",
                hover_data=["source_system", "latest_watermark"],
            ),
            width="stretch",
            key="source_acceptance_vs_quality",
        )
    st.dataframe(source, width="stretch", hide_index=True)


def aggregate_monthly(frame: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    if frame.empty or "reporting_month" not in frame.columns:
        return pd.DataFrame()
    groups = group_cols or ["reporting_month"]
    numeric_columns = [column for column in ["spend", "booked_revenue", "gross_margin", "leads", "closed_won_conversions"] if column in frame.columns]
    return frame.groupby(groups, dropna=False)[numeric_columns].sum().reset_index().sort_values(groups)


def build_funnel_summary(funnel: pd.DataFrame) -> pd.DataFrame:
    return build_stage_summary(
        sum_column(funnel, "total_leads"),
        sum_column(funnel, "mqls"),
        sum_column(funnel, "sales_qualified_leads"),
        sum_column(funnel, "conversions"),
    )


def build_stage_summary(leads: float, mqls: float, sqls: float, conversions: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"stage": "Leads", "count": leads},
            {"stage": "MQLs", "count": mqls},
            {"stage": "SQLs", "count": sqls},
            {"stage": "Conversions", "count": conversions},
        ]
    )


def build_rate_summary(funnel: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {"rate": "Lead to MQL", "value": weighted_average(funnel, "lead_to_mql_rate", "total_leads")},
        {"rate": "MQL to SQL", "value": weighted_average(funnel, "mql_to_sql_rate", "mqls")},
        {"rate": "SQL to Close", "value": weighted_average(funnel, "sql_to_close_rate", "sales_qualified_leads")},
    ]
    return pd.DataFrame(rows)


def build_funnel_by_channel(funnel: pd.DataFrame) -> pd.DataFrame:
    if funnel.empty or "normalized_channel" not in funnel.columns:
        return pd.DataFrame()
    columns = [column for column in ["total_leads", "mqls", "sales_qualified_leads", "conversions"] if column in funnel.columns]
    return funnel.groupby("normalized_channel", dropna=False)[columns].sum().reset_index()


def build_target_summary(pacing: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    frame = pacing if not pacing.empty else target
    return pd.DataFrame(
        [
            {"metric": "Target Spend", "value": sum_column(frame, "target_spend")},
            {"metric": "Actual Spend", "value": sum_column(frame, "actual_spend")},
            {"metric": "Target Revenue", "value": sum_column(frame, "target_revenue")},
            {"metric": "Actual Revenue", "value": sum_column(frame, "actual_revenue")},
        ]
    )


def build_target_monthly(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "target_month" not in frame.columns:
        return pd.DataFrame()
    columns = [column for column in ["target_revenue", "actual_revenue", "target_spend", "actual_spend"] if column in frame.columns]
    return frame.groupby("target_month", dropna=False)[columns].sum().reset_index().sort_values("target_month")


def build_channel_attainment(frame: pd.DataFrame) -> pd.DataFrame:
    channel_col = "channel" if "channel" in frame.columns else "normalized_channel"
    if frame.empty or channel_col not in frame.columns:
        return pd.DataFrame()
    output = (
        frame.groupby(channel_col, dropna=False)
        .agg(
            target_revenue=("target_revenue", "sum"),
            actual_revenue=("actual_revenue", "sum"),
            target_spend=("target_spend", "sum"),
            actual_spend=("actual_spend", "sum"),
            pacing_status=("pacing_status", lambda values: values.mode().iloc[0] if not values.mode().empty else "unknown"),
        )
        .reset_index()
        .rename(columns={channel_col: "channel"})
    )
    output["revenue_attainment"] = output.apply(lambda row: safe_divide(row["actual_revenue"], row["target_revenue"]), axis=1)
    return output


def build_region_variance(target: pd.DataFrame) -> pd.DataFrame:
    if target.empty:
        return pd.DataFrame()
    frame = target.copy()
    if "region" not in frame.columns:
        frame["region"] = "all"
    frame["region"] = frame["region"].fillna("unmapped").replace("", "unmapped")
    output = (
        frame.groupby("region", dropna=False)
        .agg(target_spend=("target_spend", "sum"), actual_spend=("actual_spend", "sum"))
        .reset_index()
    )
    output["budget_variance"] = output["actual_spend"] - output["target_spend"]
    return output


def build_missing_attribution_summary(journey: pd.DataFrame) -> pd.DataFrame:
    if journey.empty or "normalized_channel" not in journey.columns:
        return pd.DataFrame()
    frame = journey.copy()
    frame["missing_attribution_records"] = frame.get("leads_missing_attribution", 0) + frame.get(
        "conversions_missing_attribution",
        0,
    )
    return frame.groupby("normalized_channel", dropna=False)["missing_attribution_records"].sum().reset_index()


def build_quality_issue_details(quality: pd.DataFrame, source: pd.DataFrame, journey: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in quality.iterrows():
        issue_count = float(row.get("issue_count", 0) or 0)
        rejected_count = float(row.get("rejected_count", 0) or 0)
        if issue_count > 0:
            rows.append(
                {
                    "source": row.get("source_system", "unknown"),
                    "issue_type": "validation_failure",
                    "severity": "warning",
                    "count": issue_count,
                    "suggested_action": "Review validation report and rejected records.",
                }
            )
        if rejected_count > 0:
            rows.append(
                {
                    "source": row.get("source_system", "unknown"),
                    "issue_type": "rejected_records",
                    "severity": "warning",
                    "count": rejected_count,
                    "suggested_action": "Inspect rejected rows and source contract drift.",
                }
            )
    for _, row in source.iterrows():
        if str(row.get("source_health_status", "")).lower() != "healthy":
            rows.append(
                {
                    "source": row.get("source_system", "unknown"),
                    "issue_type": "source_health",
                    "severity": "warning",
                    "count": row.get("quality_issue_count", 1),
                    "suggested_action": "Check source freshness, accepted/rejected counts, and latest watermark.",
                }
            )
    if not journey.empty:
        missing = sum_column(journey, "leads_missing_attribution") + sum_column(journey, "conversions_missing_attribution")
        orphan = sum_column(journey, "orphan_conversions")
        if missing > 0:
            rows.append(
                {
                    "source": "journey_stitching",
                    "issue_type": "missing_attribution_ids",
                    "severity": "warning",
                    "count": missing,
                    "suggested_action": "Review campaign mappings and attribution ID coverage.",
                }
            )
        if orphan > 0:
            rows.append(
                {
                    "source": "sales_conversions",
                    "issue_type": "orphan_conversions",
                    "severity": "warning",
                    "count": orphan,
                    "suggested_action": "Review conversion-to-lead matching and late-arriving records.",
                }
            )
    if not rows:
        rows.append(
            {
                "source": "all",
                "issue_type": "none",
                "severity": "healthy",
                "count": 0,
                "suggested_action": "No current dashboard-level issues in the loaded marts.",
            }
        )
    return pd.DataFrame(rows)


def status_counts(frame: pd.DataFrame, column: str, count_name: str) -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return pd.DataFrame(columns=[column, count_name])
    output = frame[column].fillna("unknown").value_counts().reset_index()
    output.columns = [column, count_name]
    return output


def weighted_average(frame: pd.DataFrame, value_column: str, weight_column: str) -> float:
    if frame.empty or value_column not in frame.columns:
        return 0.0
    values = pd.to_numeric(frame[value_column], errors="coerce").fillna(0)
    if weight_column not in frame.columns:
        return float(values.mean()) if len(values) else 0.0
    weights = pd.to_numeric(frame[weight_column], errors="coerce").fillna(0)
    return safe_divide(float((values * weights).sum()), float(weights.sum()))


def most_common_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "Unknown"
    values = frame[column].dropna()
    if values.empty:
        return "Unknown"
    return str(values.mode().iloc[0]).replace("_", " ").title()


def sort_if_possible(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return frame
    return frame.sort_values(available, ascending=[False] * len(available))


def melt_existing(
    frame: pd.DataFrame,
    id_vars: list[str],
    value_vars: list[str],
    var_name: str,
    value_name: str,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    ids = [column for column in id_vars if column in frame.columns]
    values = [column for column in value_vars if column in frame.columns]
    if not ids or not values:
        return pd.DataFrame()
    return frame.melt(id_vars=ids, value_vars=values, var_name=var_name, value_name=value_name)


def _has_columns(frame: pd.DataFrame, columns: list[str]) -> bool:
    return not frame.empty and all(column in frame.columns for column in columns)


if __name__ == "__main__":
    main()
