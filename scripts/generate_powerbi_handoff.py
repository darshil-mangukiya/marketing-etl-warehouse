from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_powerbi_semantic_model import semantic_model_spec

POWERBI_ROOT = PROJECT_ROOT / "dashboards" / "powerbi"
DATA_DIR = POWERBI_ROOT / "data"
HANDOFF_ROOT = PROJECT_ROOT / "data" / "exports" / "powerbi_handoff"
PROJECT_NAME = "Campaign ROI Reporting Automation & Marketing Performance Analytics Platform"


def _read_export(name: str) -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "exports" / f"demo_{name}.csv"
    if not path.exists():
        path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _write_csv(name: str, frame: pd.DataFrame, manifest: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / f"{name}.csv"
    frame.to_csv(output_path, index=False)
    manifest.append({"table": name, "row_count": len(frame), "file": str(output_path.relative_to(PROJECT_ROOT))})


def _dim_date(frames: list[pd.DataFrame]) -> pd.DataFrame:
    values: list[pd.Timestamp] = []
    for frame in frames:
        for column in ("reporting_month", "target_month", "snapshot_month", "created_at"):
            if column in frame.columns:
                values.extend(pd.to_datetime(frame[column], errors="coerce").dropna().tolist())
    if not values:
        values = [pd.Timestamp("2026-01-01")]
    months = pd.date_range(min(values).to_period("M").to_timestamp(), max(values).to_period("M").to_timestamp(), freq="MS")
    return pd.DataFrame(
        {
            "date_day": months.strftime("%Y-%m-%d"),
            "year": months.year,
            "quarter": "Q" + months.quarter.astype(str),
            "month_number": months.month,
            "month_name": months.strftime("%B"),
            "week_of_year": months.isocalendar().week.astype(int),
        }
    )


def _dim_channel(channel: pd.DataFrame, campaign: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for frame in (channel, campaign):
        if frame.empty or "normalized_channel" not in frame.columns:
            continue
        for value in sorted(frame["normalized_channel"].dropna().astype(str).unique()):
            rows.append(
                {
                    "channel_key": value,
                    "channel_name": value.replace("_", " ").title(),
                    "channel_group": "Paid" if value in {"paid_search", "paid_social"} else "Owned/Other",
                }
            )
    output = pd.DataFrame(rows).drop_duplicates("channel_key")
    return output if not output.empty else pd.DataFrame(columns=["channel_key", "channel_name", "channel_group"])


def _dim_campaign(campaign: pd.DataFrame) -> pd.DataFrame:
    if campaign.empty:
        return pd.DataFrame(
            columns=[
                "campaign_key",
                "campaign_id",
                "canonical_campaign_name",
                "canonical_channel",
                "owner_team",
                "valid_from",
                "valid_to",
                "is_current",
            ]
        )
    frame = campaign[["campaign_id", "campaign_name", "normalized_channel"]].drop_duplicates("campaign_id").copy()
    frame["campaign_key"] = frame["campaign_id"]
    frame["canonical_campaign_name"] = frame["campaign_name"]
    frame["canonical_channel"] = frame["normalized_channel"]
    frame["owner_team"] = "growth_marketing"
    frame["valid_from"] = "2026-01-01"
    frame["valid_to"] = ""
    frame["is_current"] = True
    return frame[
        [
            "campaign_key",
            "campaign_id",
            "canonical_campaign_name",
            "canonical_channel",
            "owner_team",
            "valid_from",
            "valid_to",
            "is_current",
        ]
    ]


def _dim_customer(customer: pd.DataFrame) -> pd.DataFrame:
    if customer.empty:
        return pd.DataFrame(columns=["customer_key", "customer_id", "lead_id", "customer_segment", "is_current"])
    frame = customer.copy()
    frame["customer_key"] = frame["customer_id"]
    frame["lead_id"] = ""
    frame["is_current"] = True
    return frame[["customer_key", "customer_id", "lead_id", "customer_segment", "is_current"]].drop_duplicates("customer_key")


def _dim_region(target: pd.DataFrame, regional: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for frame in (target, regional):
        if frame.empty or "region" not in frame.columns:
            continue
        for value in sorted(frame["region"].dropna().astype(str).unique()):
            rows.append({"region_key": value, "country": "MULTI", "region": value, "sales_territory": value})
    output = pd.DataFrame(rows).drop_duplicates("region_key")
    return output if not output.empty else pd.DataFrame(columns=["region_key", "country", "region", "sales_territory"])


def _normalize_mart_columns(name: str, frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if name in {"mart_channel_performance", "mart_funnel_performance"} and "normalized_channel" in output.columns:
        output["channel_key"] = output["normalized_channel"]
        output["channel_name"] = output.get("channel_name", output["normalized_channel"].str.replace("_", " ").str.title())
        output["channel_group"] = output["normalized_channel"].map(
            lambda value: "Paid" if value in {"paid_search", "paid_social"} else "Owned/Other"
        )
    if name == "mart_target_vs_actual" and "channel" in output.columns and "channel_name" not in output.columns:
        output["channel_name"] = output["channel"].astype(str).str.replace("_", " ").str.title()
    return output


def _dax_measures() -> str:
    spec = semantic_model_spec()
    lines = [
        f"// {PROJECT_NAME}",
        "// Paste these measures into a dedicated Power BI Measures table.",
        "// Each measure comment references semantic/kpi_catalog.yml where a governed KPI key exists.",
        "",
    ]
    kpi_lookup = {
        "Total Spend": "total_spend",
        "Booked Revenue": "booked_revenue",
        "Gross Margin": "gross_margin",
        "ROAS": "roas",
        "Marketing Efficiency Ratio": "marketing_efficiency_ratio",
        "Total Clicks": "total_clicks",
        "Total Impressions": "total_impressions",
        "Click Through Rate": "click_through_rate",
        "Total Leads": "total_leads",
        "Qualified Leads": "qualified_leads",
        "Closed Won Conversions": "closed_won_conversions",
        "CAC": "cac",
        "Cost Per Lead": "cost_per_lead",
        "Campaign Spend": "campaign_spend",
        "Attributed Revenue": "attributed_revenue",
        "Attributed ROAS": "attributed_roas",
        "Waste Campaigns": "waste_campaigns",
        "Lead to MQL Rate": "lead_to_mql_rate",
        "SQL to Close Rate": "sql_to_close_rate",
        "Revenue Attainment": "revenue_attainment",
        "Spend Attainment": "spend_attainment",
        "Open Actions": "open_actions",
        "P0 Actions": "p0_actions",
        "Average Data Product Score": "data_product_score",
        "Certified KPIs": "certified_kpis",
        "GA4 Sessions": "ga4_sessions",
        "GA4 Purchases": "ga4_purchases",
        "GA4 Purchase Revenue": "ga4_purchase_revenue",
        "High Variance Drivers": "high_variance_drivers",
        "ROAS Absolute Variance": "roas_absolute_variance",
        "Campaign Actions": "campaign_actions",
        "Campaigns to Scale": "campaigns_to_scale",
        "Data Quality Holds": "data_quality_holds",
    }
    current_folder = None
    for table in spec["tables"]:
        for measure_name, expression, _format, folder in table.get("measures", []):
            if folder != current_folder:
                lines.append(f"// {folder}")
                current_folder = folder
            key = kpi_lookup.get(measure_name, "supporting_metric")
            lines.append(f"// kpi_catalog_key: {key}")
            lines.append(f"{measure_name} = {expression}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_powerbi_handoff() -> dict:
    POWERBI_ROOT.mkdir(parents=True, exist_ok=True)
    (POWERBI_ROOT / "screenshots").mkdir(parents=True, exist_ok=True)
    (POWERBI_ROOT / "exports").mkdir(parents=True, exist_ok=True)
    spec = semantic_model_spec()
    channel = _read_export("mart_channel_performance")
    campaign = _read_export("mart_campaign_performance")
    target = _read_export("mart_target_vs_actual")
    funnel = _read_export("mart_funnel_performance")
    attribution = _read_export("mart_attribution_model_comparison")
    customer = _read_export("mart_customer_value")
    customer_segment = _read_export("mart_customer_segment_mix")
    device = _read_export("mart_device_performance")
    regional = _read_export("mart_regional_performance")
    action_recommendations = pd.read_csv(PROJECT_ROOT / "data" / "exports" / "analyst_outputs" / "campaign_action_recommendations.csv") if (PROJECT_ROOT / "data" / "exports" / "analyst_outputs" / "campaign_action_recommendations.csv").exists() else pd.DataFrame()

    manifest: list[dict] = []
    tables = {
        "dim_date": _dim_date([channel, target, funnel, attribution]),
        "dim_campaign": _dim_campaign(campaign),
        "dim_channel": _dim_channel(channel, campaign),
        "dim_customer": _dim_customer(customer),
        "dim_region": _dim_region(target, regional),
    }
    for table in spec["tables"]:
        name = table["name"]
        if name not in tables:
            tables[name] = _normalize_mart_columns(name, _read_export(name))
        _write_csv(name, tables[name], manifest)

    relationships = [
        "dim_channel.channel_key -> mart_channel_performance.channel_key | many-to-one | single",
        "dim_channel.channel_key -> mart_funnel_performance.channel_key | many-to-one | single",
        "dim_date.date_day -> mart_channel_performance.reporting_month | many-to-one | single",
        "dim_date.date_day -> mart_funnel_performance.reporting_month | many-to-one | single",
        "dim_date.date_day -> mart_target_vs_actual.target_month | many-to-one | single",
        "dim_campaign.campaign_id -> mart_campaign_performance.campaign_id | many-to-one | single",
        "dim_region.region -> mart_target_vs_actual.region | many-to-one | single",
        "dim_date.date_day -> mart_ga4_funnel.event_date | many-to-one | single",
        "dim_campaign.campaign_id -> mart_ga4_funnel.campaign_id | many-to-one | single",
        "dim_channel.channel_key -> mart_marketing_variance_drivers.channel_key | many-to-one | single",
        "dim_campaign.campaign_id -> mart_campaign_action_center.campaign_id | many-to-one | single",
    ]

    (POWERBI_ROOT / "dax_measures.dax").write_text(_dax_measures(), encoding="utf-8")
    _write_powerbi_docs(spec, relationships, manifest)
    handoff_manifest = _write_import_ready_handoff(
        tables=tables,
        channel=channel,
        campaign=campaign,
        funnel=funnel,
        target=target,
        attribution=attribution,
        customer_segment=customer_segment,
        device=device,
        action_recommendations=action_recommendations,
        relationships=relationships,
    )
    handoff_manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "table_count": len(manifest),
        "measure_count": len(re.findall(r"^[A-Za-z0-9][^=\n]+?\s=", _dax_measures(), flags=re.MULTILINE)),
        "relationship_count": len(relationships),
        "tables": manifest,
        "import_ready_handoff": handoff_manifest,
    }
    (POWERBI_ROOT / "powerbi_handoff_manifest.json").write_text(json.dumps(handoff_manifest, indent=2), encoding="utf-8")
    return handoff_manifest


def _handoff_write_csv(name: str, frame: pd.DataFrame, manifest: list[dict]) -> None:
    HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = HANDOFF_ROOT / f"{name}.csv"
    frame.to_csv(output_path, index=False)
    manifest.append({"table": name, "row_count": len(frame), "file": str(output_path.relative_to(PROJECT_ROOT))})


def _write_import_ready_handoff(
    tables: dict[str, pd.DataFrame],
    channel: pd.DataFrame,
    campaign: pd.DataFrame,
    funnel: pd.DataFrame,
    target: pd.DataFrame,
    attribution: pd.DataFrame,
    customer_segment: pd.DataFrame,
    device: pd.DataFrame,
    action_recommendations: pd.DataFrame,
    relationships: list[str],
) -> dict:
    HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    dim_device = (
        device[["device"]].drop_duplicates().assign(device_key=lambda frame: frame["device"])
        if not device.empty and "device" in device.columns
        else pd.DataFrame(columns=["device_key", "device"])
    )
    dim_customer_segment = (
        customer_segment[["customer_segment"]].drop_duplicates().assign(customer_segment_key=lambda frame: frame["customer_segment"])
        if not customer_segment.empty and "customer_segment" in customer_segment.columns
        else pd.DataFrame(columns=["customer_segment_key", "customer_segment"])
    )
    fact_ad_spend = campaign[[column for column in ["campaign_id", "campaign_name", "normalized_channel", "spend", "impressions", "clicks", "conversions"] if column in campaign.columns]].copy()
    fact_leads = funnel.copy()
    fact_conversions = funnel[[column for column in ["reporting_month", "normalized_channel", "conversions", "sql_to_close_rate"] if column in funnel.columns]].copy()
    fact_revenue_attribution = attribution.copy()
    fact_budget_targets = target.copy()
    handoff_tables = {
        "dim_date": tables.get("dim_date", pd.DataFrame()),
        "dim_campaign": tables.get("dim_campaign", pd.DataFrame()),
        "dim_channel": tables.get("dim_channel", pd.DataFrame()),
        "dim_region": tables.get("dim_region", pd.DataFrame()),
        "dim_device": dim_device,
        "dim_customer_segment": dim_customer_segment,
        "fact_campaign_performance": campaign,
        "fact_ad_spend": fact_ad_spend,
        "fact_leads": fact_leads,
        "fact_conversions": fact_conversions,
        "fact_revenue_attribution": fact_revenue_attribution,
        "fact_budget_targets": fact_budget_targets,
        "mart_campaign_action_recommendations": action_recommendations,
        "mart_budget_scenarios": tables.get("mart_budget_scenarios", pd.DataFrame()),
    }
    for name, frame in handoff_tables.items():
        _handoff_write_csv(name, frame, manifest)

    relationship_text = "\n".join(
        [
            "- dim_date.date_day -> fact_campaign_performance.reporting_month | many-to-one | single direction",
            "- dim_campaign.campaign_id -> fact_campaign_performance.campaign_id | many-to-one | single direction",
            "- dim_channel.channel_key -> fact_campaign_performance.normalized_channel | many-to-one | single direction",
            "- dim_channel.channel_key -> fact_leads.normalized_channel | many-to-one | single direction",
            "- dim_region.region -> fact_budget_targets.region | many-to-one | single direction",
            "- dim_campaign.campaign_id -> mart_campaign_action_recommendations.campaign_id | many-to-one | single direction",
            "",
            "Additional existing semantic relationships:",
            *[f"- {relationship}" for relationship in relationships],
        ]
    )
    (HANDOFF_ROOT / "README.md").write_text(
        "# Power BI Handoff Package\n\n"
        "Import this folder into Power BI Desktop using Get Data > Folder. The CSVs are generated by the local project pipeline and are designed for import-mode report building.\n\n"
        "Dimensions: `dim_date`, `dim_campaign`, `dim_channel`, `dim_region`, `dim_device`, `dim_customer_segment`.\n\n"
        "Facts/marts: `fact_campaign_performance`, `fact_ad_spend`, `fact_leads`, `fact_conversions`, `fact_revenue_attribution`, `fact_budget_targets`, `mart_campaign_action_recommendations`, `mart_budget_scenarios`.\n\n"
        "This handoff folder ships CSV import tables and build documentation that complement the completed editable dashboard "
        "at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`. Page captures live in `evidence/screenshots/powerbi/`; "
        "rebuild guidance lives in `powerbi_build_steps.md` and `screenshot_checklist.md`.\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "relationships.md").write_text("# Relationships\n\n" + relationship_text + "\n", encoding="utf-8")
    (HANDOFF_ROOT / "dax_measures.md").write_text(
        "# DAX Measures\n\n```DAX\n" + _dax_measures() + "```\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "powerbi_build_steps.md").write_text(
        "# Power BI Build Steps\n\n"
        "1. Open Power BI Desktop.\n"
        "2. Select Get Data > Folder and choose `data/exports/powerbi_handoff/`.\n"
        "3. Load each CSV as a separate table.\n"
        "4. Set date fields to Date, metric fields to Decimal Number or Whole Number, and keys to Text.\n"
        "5. Create relationships from `relationships.md` with single-direction filters.\n"
        "6. Create a Measures table and paste measures from `dax_measures.md`.\n"
        "7. Preserve the seven evidenced PBIX pages and assemble the Power BI-ready analytical pages from `page_specs.md`.\n"
        "8. Refresh screenshot evidence from `screenshot_checklist.md`.\n"
        "9. Save the editable report as `p2_marketing_performance_dashboard.pbix`.\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "page_specs.md").write_text(
        "# Page Specs\n\n"
        "1. Executive Marketing Overview: spend, revenue, ROAS, CAC, target status, source-health status.\n"
        "2. Channel Performance: channel spend, leads, conversions, ROAS, CAC, trend and rank visuals.\n"
        "3. Campaign ROI Deep Dive: campaign table, ROI flags, action recommendations, drill-through detail.\n"
        "4. Funnel Conversion: lead, MQL, SQL, and close-rate drop-off visuals.\n"
        "5. Budget Pacing & Targets: spend/revenue attainment, pacing status, variance table.\n"
        "6. Attribution & Customer Value: attribution model comparison and customer segment value.\n"
        "7. Data Quality & Refresh Health: rejected rows, source health, validation warnings, refresh notes.\n"
        "8. GA4 Funnel: session and ecommerce-stage drop-off by source, campaign and device.\n"
        "9. Performance Drivers and Action Center: diagnostic variance plus human-reviewed actions.\n"
        "10. Scenario Planning: explicit assumptions, projected outcomes and target variance.\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "measure_table_setup.md").write_text(
        "# Measure Table Setup\n\nCreate an empty table named `Measures`, hide any placeholder column, then paste the DAX measures from `dax_measures.md`. Use folders matching the DAX comments: Spend/Revenue, ROI/Efficiency, Funnel, Targets, Attribution, Governance, and Data Quality.\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "power_query_steps.md").write_text(
        "# Power Query Steps\n\n"
        "- Keep source file names as table names.\n"
        "- Promote headers and set explicit data types.\n"
        "- Do not calculate governed KPIs in Power Query; use DAX measures.\n"
        "- Keep data provenance visible in report notes.\n",
        encoding="utf-8",
    )
    (HANDOFF_ROOT / "screenshot_checklist.md").write_text(
        "# Screenshot Checklist\n\n"
        "Completed dashboard captures are committed at `evidence/screenshots/powerbi/`. "
        "To refresh screenshot evidence after editing the `.pbix`, capture:\n\n"
        "- executive overview\n"
        "- channel performance\n"
        "- campaign ROI\n"
        "- funnel conversion\n"
        "- budget pacing targets\n"
        "- attribution customer value\n"
        "- data quality refresh health\n"
        "- model view\n"
        "- relationships view\n"
        "- measure table\n"
        "- Power Query steps\n",
        encoding="utf-8",
    )
    return {"table_count": len(manifest), "tables": manifest, "folder": str(HANDOFF_ROOT.relative_to(PROJECT_ROOT))}


def _write_powerbi_docs(spec: dict, relationships: list[str], manifest: list[dict]) -> None:
    table_list = "\n".join(f"- `{row['file']}`: `{row['table']}` ({row['row_count']:,} rows)" for row in manifest)
    page_list = "\n".join(
        f"- **{page['page']}**: {page['business_question']} Filters: {', '.join(page['filters'])}."
        for page in spec["dashboard_pages"]
    )
    relationship_list = "\n".join(f"- {relationship}" for relationship in relationships)
    (POWERBI_ROOT / "README.md").write_text(
        "# Power BI Dashboard\n\n"
        "This folder contains the completed Power BI dashboard and its source-controlled inputs.\n\n"
        "## Dashboard File\n\n"
        "- `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`\n\n"
        "This is the editable Power BI Desktop dashboard file. Open it in Power BI Desktop to review or extend the report.\n\n"
        "## Data Sources\n\n"
        "The dashboard is built from the exported CSV marts in `dashboards/powerbi/data/`:\n\n"
        f"{table_list}\n\n"
        "## Dashboard Pages\n\n"
        "1. Executive Overview\n"
        "2. Channel Performance\n"
        "3. Campaign ROI\n"
        "4. Funnel Analysis\n"
        "5. Attribution Model Comparison\n"
        "6. Target vs Actual\n"
        "7. Data Quality & Source Health\n\n"
        "## Screenshots\n\n"
        "Page captures are stored in `evidence/screenshots/powerbi/`:\n\n"
        "- `executive_overview.png`\n"
        "- `channel_performance.png`\n"
        "- `campaign_roi.png`\n"
        "- `funnel_analysis.png`\n"
        "- `attribution_model_comparison.png`\n"
        "- `target_vs_actual.png`\n"
        "- `data_quality_source_health.png`\n\n"
        "## Notes\n\n"
        "- All report data is generated by the local project pipeline.\n"
        "- The committed report is an editable Power BI Desktop `.pbix`; cloud publishing and managed refresh are deployment extensions.\n"
        "- Measures are built from the exported CSV marts listed above.\n"
        "- The `.pbix` file is the editable dashboard; the dashboard is intended as local project evidence.\n"
        "- Supporting model documentation lives alongside this README: `data_model.md`, `semantic_model.md`, "
        "`relationship_map.md`, `dax_measures.dax`, `power_query_steps.md`, `dashboard_spec.md`, `BUILD_CHECKLIST.md`, "
        "`refresh_guide.md`, `performance_optimization.md`, and `rls_mockup.md`.\n",
        encoding="utf-8",
    )
    (DATA_DIR / "README.md").write_text(
        "# Power BI Import Data\n\n"
        "Import this folder in Power BI Desktop with **Get Data > Folder**. Each CSV maps to one semantic table.\n\n"
        f"{table_list}\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "relationship_map.md").write_text(
        "# Relationship Map\n\n" + relationship_list + "\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "data_model.md").write_text(
        "# Data Model\n\n"
        "Import mode star schema with conformed date, channel, campaign, customer, and region dimensions. "
        "Relationships are single-direction from dimensions to marts to keep filter behavior predictable.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "semantic_model.md").write_text(
        "# Semantic Model\n\n"
        "Use a dedicated Measures table. Measure definitions come from `dax_measures.dax` and reference `semantic/kpi_catalog.yml` keys in comments.\n\n"
        f"Semantic tables: {len(manifest)}. Relationship definitions: {len(relationships)}.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "dashboard_spec.md").write_text(
        "# Dashboard Spec\n\n" + page_list + "\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "power_query_steps.md").write_text(
        "# Power Query Steps\n\n"
        "1. Get Data > Folder and select `dashboards/powerbi/data/`.\n"
        "2. Combine files disabled: load each CSV as a separate table.\n"
        "3. Set date fields to Date, numeric metric fields to Decimal Number or Whole Number, and key fields to Text.\n"
        "4. Disable auto date/time and create relationships manually from `relationship_map.md`.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "performance_optimization.md").write_text(
        "# Performance Optimization\n\n"
        "Use import mode, hide technical keys after relationships are created, avoid bi-directional filters, "
        "format measures rather than calculated columns where possible, and keep drill-through pages filtered by campaign/channel/date.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "refresh_guide.md").write_text(
        "# Refresh Guide\n\n"
        "Regenerate the project exports with `make powerbi-exports`, then refresh the folder source in Power BI Desktop. "
        "For a published report, replace local file paths with a OneDrive, SharePoint, or workspace dataflow path.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "rls_mockup.md").write_text(
        "# Row-Level Security Mockup\n\n"
        "Suggested roles: Executive All Access, Regional Marketing, Channel Owner, Finance Viewer, and Data Quality Reviewer. "
        "Apply filters on `dim_region[region]` and `dim_channel[channel_key]` after validating stakeholder access rules.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "BUILD_CHECKLIST.md").write_text(
        "# Build Checklist\n\n"
        "1. Open Power BI Desktop.\n"
        "2. Get Data > Folder > select `dashboards/powerbi/data/`.\n"
        "3. Load each CSV as a separate table.\n"
        "4. Set key columns to Text, date columns to Date, and metric columns to Decimal Number or Whole Number.\n"
        "5. Create a Measures table.\n"
        "6. Paste all measures from `dax_measures.dax`.\n"
        "7. Create the relationships in `relationship_map.md` with single-direction filtering.\n"
        "8. Build seven pages: Executive Marketing Overview, Channel Performance, Campaign ROI Deep Dive, Funnel Conversion, Budget Pacing & Targets, Attribution & Customer Value, and Data Quality & Refresh Health.\n"
        "9. Add slicers for date, channel, campaign, region, device/platform where available, and customer segment.\n"
        "10. Add campaign drill-through, a tooltip page, and conditional formatting for ROAS, pacing, data quality, and action priority.\n"
        "11. Capture screenshots listed in `screenshots/SHOT_LIST.md`.\n"
        "12. Save as `p2_marketing_performance_dashboard.pbix` and export PDF from Power BI Desktop if needed. "
        "The completed dashboard file is committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`.\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "screenshots" / "SHOT_LIST.md").write_text(
        "# Screenshot Shot List\n\n"
        "Completed page captures are committed at `evidence/screenshots/powerbi/`. "
        "To refresh screenshot evidence after editing the `.pbix`, capture:\n"
        "- `01_executive_marketing_overview.png`\n"
        "- `02_channel_performance.png`\n"
        "- `03_campaign_roi_deep_dive.png`\n"
        "- `04_funnel_conversion.png`\n"
        "- `05_budget_pacing_targets.png`\n"
        "- `06_attribution_customer_value.png`\n"
        "- `07_data_quality_refresh_health.png`\n"
        "- `08_campaign_drillthrough.png`\n"
        "- `09_tooltip_page.png`\n",
        encoding="utf-8",
    )
    (POWERBI_ROOT / "exports" / "README.md").write_text(
        "# Optional Desktop Exports\n\n"
        "The completed dashboard is committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`. "
        "Export a PDF from Power BI Desktop when a static review artifact is useful.\n",
        encoding="utf-8",
    )


def main() -> None:
    print(json.dumps(generate_powerbi_handoff(), indent=2))


if __name__ == "__main__":
    main()
