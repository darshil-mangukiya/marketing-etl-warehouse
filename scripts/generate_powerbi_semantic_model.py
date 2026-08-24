from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "semantic_layer" / "powerbi_tmdl"


def semantic_model_spec() -> dict:
    return {
        "model_name": "Marketing ETL Semantic Model",
        "compatibility_level": 1601,
        "tables": [
            {
                "name": "dim_date",
                "description": "Conformed date dimension used for campaign, lead, conversion, and target analysis.",
                "columns": [
                    ("date_day", "dateTime"),
                    ("year", "int64"),
                    ("quarter", "string"),
                    ("month_number", "int64"),
                    ("month_name", "string"),
                    ("week_of_year", "int64"),
                ],
            },
            {
                "name": "dim_campaign",
                "description": "SCD Type 2-style campaign dimension with canonical names and owner teams.",
                "columns": [
                    ("campaign_key", "string"),
                    ("campaign_id", "string"),
                    ("canonical_campaign_name", "string"),
                    ("canonical_channel", "string"),
                    ("owner_team", "string"),
                    ("valid_from", "dateTime"),
                    ("valid_to", "dateTime"),
                    ("is_current", "boolean"),
                ],
                "hidden_columns": ["campaign_key"],
            },
            {
                "name": "dim_channel",
                "description": "Conformed marketing channel dimension for paid search, paid social, email, organic, direct, referral, and unknown traffic.",
                "columns": [
                    ("channel_key", "string"),
                    ("channel_name", "string"),
                    ("channel_group", "string"),
                ],
                "hidden_columns": ["channel_key"],
            },
            {
                "name": "dim_customer",
                "description": "Customer and lead identity dimension prepared for LTV and segmentation reporting.",
                "columns": [
                    ("customer_key", "string"),
                    ("customer_id", "string"),
                    ("lead_id", "string"),
                    ("customer_segment", "string"),
                    ("is_current", "boolean"),
                ],
                "hidden_columns": ["customer_key"],
            },
            {
                "name": "dim_region",
                "description": "Conformed region and sales territory dimension.",
                "columns": [
                    ("region_key", "string"),
                    ("country", "string"),
                    ("region", "string"),
                    ("sales_territory", "string"),
                ],
                "hidden_columns": ["region_key"],
            },
            {
                "name": "mart_channel_performance",
                "description": "Executive channel performance mart for spend, revenue, ROAS, CAC, and funnel KPIs.",
                "columns": [
                    ("reporting_month", "dateTime"),
                    ("normalized_channel", "string"),
                    ("channel_key", "string"),
                    ("channel_name", "string"),
                    ("channel_group", "string"),
                    ("spend", "decimal"),
                    ("impressions", "int64"),
                    ("clicks", "int64"),
                    ("platform_conversions", "int64"),
                    ("leads", "int64"),
                    ("qualified_leads", "int64"),
                    ("closed_won_conversions", "int64"),
                    ("booked_revenue", "decimal"),
                    ("gross_margin", "decimal"),
                    ("ctr", "decimal"),
                    ("cpc", "decimal"),
                    ("cac", "decimal"),
                    ("roas", "decimal"),
                    ("mer", "decimal"),
                ],
                "hidden_columns": ["channel_key"],
                "measures": [
                    ("Total Spend", "SUM('mart_channel_performance'[spend])", "$#,0", "Executive KPIs"),
                    ("Booked Revenue", "SUM('mart_channel_performance'[booked_revenue])", "$#,0", "Executive KPIs"),
                    ("Gross Margin", "SUM('mart_channel_performance'[gross_margin])", "$#,0", "Executive KPIs"),
                    ("ROAS", "DIVIDE([Booked Revenue], [Total Spend])", "0.00x", "Executive KPIs"),
                    ("Marketing Efficiency Ratio", "DIVIDE([Gross Margin], [Total Spend])", "0.00x", "Executive KPIs"),
                    ("Total Clicks", "SUM('mart_channel_performance'[clicks])", "#,0", "Engagement"),
                    ("Total Impressions", "SUM('mart_channel_performance'[impressions])", "#,0", "Engagement"),
                    ("Click Through Rate", "DIVIDE([Total Clicks], [Total Impressions])", "0.00%", "Engagement"),
                    ("Total Leads", "SUM('mart_channel_performance'[leads])", "#,0", "Funnel"),
                    ("Qualified Leads", "SUM('mart_channel_performance'[qualified_leads])", "#,0", "Funnel"),
                    ("Closed Won Conversions", "SUM('mart_channel_performance'[closed_won_conversions])", "#,0", "Funnel"),
                    ("CAC", "DIVIDE([Total Spend], [Closed Won Conversions])", "$#,0", "Efficiency"),
                    ("Cost Per Lead", "DIVIDE([Total Spend], [Total Leads])", "$#,0", "Efficiency"),
                ],
            },
            {
                "name": "mart_campaign_performance",
                "description": "Campaign intelligence mart for waste budget detection and campaign-level ROI.",
                "columns": [
                    ("campaign_id", "string"),
                    ("campaign_name", "string"),
                    ("normalized_channel", "string"),
                    ("spend", "decimal"),
                    ("impressions", "int64"),
                    ("clicks", "int64"),
                    ("conversions", "int64"),
                    ("attributed_revenue", "decimal"),
                    ("attributed_roas", "decimal"),
                    ("waste_budget_flag", "boolean"),
                ],
                "measures": [
                    ("Campaign Spend", "SUM('mart_campaign_performance'[spend])", "$#,0", "Campaign Intelligence"),
                    ("Attributed Revenue", "SUM('mart_campaign_performance'[attributed_revenue])", "$#,0", "Campaign Intelligence"),
                    ("Attributed ROAS", "DIVIDE([Attributed Revenue], [Campaign Spend])", "0.00x", "Campaign Intelligence"),
                    ("Waste Campaigns", "CALCULATE(DISTINCTCOUNT('mart_campaign_performance'[campaign_id]), 'mart_campaign_performance'[waste_budget_flag] = TRUE())", "#,0", "Campaign Intelligence"),
                ],
            },
            {
                "name": "mart_funnel_performance",
                "description": "Monthly lead funnel mart by channel.",
                "columns": [
                    ("reporting_month", "dateTime"),
                    ("normalized_channel", "string"),
                    ("channel_key", "string"),
                    ("channel_name", "string"),
                    ("channel_group", "string"),
                    ("total_leads", "int64"),
                    ("mqls", "int64"),
                    ("sales_accepted_leads", "int64"),
                    ("sales_qualified_leads", "int64"),
                    ("conversions", "decimal"),
                    ("lead_to_mql_rate", "decimal"),
                    ("mql_to_sql_rate", "decimal"),
                    ("sql_to_close_rate", "decimal"),
                ],
                "hidden_columns": ["channel_key"],
                "measures": [
                    ("Funnel Leads", "SUM('mart_funnel_performance'[total_leads])", "#,0", "Funnel"),
                    ("Funnel MQLs", "SUM('mart_funnel_performance'[mqls])", "#,0", "Funnel"),
                    ("Funnel SQLs", "SUM('mart_funnel_performance'[sales_qualified_leads])", "#,0", "Funnel"),
                    ("Lead to MQL Rate", "DIVIDE([Funnel MQLs], [Funnel Leads])", "0.00%", "Funnel"),
                    ("SQL to Close Rate", "DIVIDE(SUM('mart_funnel_performance'[conversions]), [Funnel SQLs])", "0.00%", "Funnel"),
                ],
            },
            {
                "name": "mart_target_vs_actual",
                "description": "Monthly target attainment by region, channel, and budget owner.",
                "columns": [
                    ("source_system", "string"),
                    ("batch_id", "string"),
                    ("target_month", "dateTime"),
                    ("region", "string"),
                    ("channel", "string"),
                    ("channel_name", "string"),
                    ("target_spend", "decimal"),
                    ("actual_spend", "decimal"),
                    ("spend_attainment", "decimal"),
                    ("target_revenue", "decimal"),
                    ("actual_revenue", "decimal"),
                    ("revenue_attainment", "decimal"),
                    ("target_leads", "int64"),
                    ("target_conversions", "int64"),
                    ("actual_leads", "int64"),
                    ("lead_attainment", "decimal"),
                    ("budget_owner", "string"),
                    ("ingestion_available_at", "dateTime"),
                    ("reporting_month", "dateTime"),
                    ("normalized_channel", "string"),
                ],
                "measures": [
                    ("Target Revenue", "SUM('mart_target_vs_actual'[target_revenue])", "$#,0", "Targets"),
                    ("Actual Revenue", "SUM('mart_target_vs_actual'[actual_revenue])", "$#,0", "Targets"),
                    ("Revenue Attainment", "DIVIDE([Actual Revenue], [Target Revenue])", "0.00%", "Targets"),
                    ("Target Spend", "SUM('mart_target_vs_actual'[target_spend])", "$#,0", "Targets"),
                    ("Actual Spend", "SUM('mart_target_vs_actual'[actual_spend])", "$#,0", "Targets"),
                    ("Spend Attainment", "DIVIDE([Actual Spend], [Target Spend])", "0.00%", "Targets"),
                ],
            },
            {
                "name": "mart_attribution_model_comparison",
                "description": "Attribution model comparison for explaining why ROI changes across reporting methods.",
                "columns": [
                    ("reporting_month", "dateTime"),
                    ("first_touch_revenue", "decimal"),
                    ("last_touch_revenue", "decimal"),
                    ("linear_revenue", "decimal"),
                    ("u_shaped_revenue", "decimal"),
                    ("time_decay_revenue", "decimal"),
                    ("position_based_revenue", "decimal"),
                    ("last_vs_first_revenue_delta", "decimal"),
                    ("time_decay_vs_linear_revenue_delta", "decimal"),
                    ("u_shaped_vs_linear_revenue_delta", "decimal"),
                ],
                "measures": [
                    ("First Touch Revenue", "SUM('mart_attribution_model_comparison'[first_touch_revenue])", "$#,0", "Attribution"),
                    ("Last Touch Revenue", "SUM('mart_attribution_model_comparison'[last_touch_revenue])", "$#,0", "Attribution"),
                    ("Linear Revenue", "SUM('mart_attribution_model_comparison'[linear_revenue])", "$#,0", "Attribution"),
                    ("Time Decay Revenue", "SUM('mart_attribution_model_comparison'[time_decay_revenue])", "$#,0", "Attribution"),
                    ("Last vs First Revenue Delta", "SUM('mart_attribution_model_comparison'[last_vs_first_revenue_delta])", "$#,0", "Attribution"),
                ],
            },
            {
                "name": "mart_action_center",
                "description": "Operational action queue created from campaign optimization, pacing, quality, source-health, anomaly, forecast, and scenario signals.",
                "columns": [
                    ("action_id", "string"),
                    ("priority", "string"),
                    ("action_type", "string"),
                    ("owner_team", "string"),
                    ("source_area", "string"),
                    ("normalized_channel", "string"),
                    ("title", "string"),
                    ("recommended_action", "string"),
                    ("business_impact", "string"),
                    ("evidence_metric", "string"),
                    ("due_in_days", "int64"),
                    ("action_value", "decimal"),
                    ("status", "string"),
                    ("created_at", "dateTime"),
                ],
                "measures": [
                    ("Open Actions", "COUNTROWS('mart_action_center')", "#,0", "Governance"),
                    ("P0 Actions", "CALCULATE([Open Actions], 'mart_action_center'[priority] = \"P0\")", "#,0", "Governance"),
                    ("P1 Actions", "CALCULATE([Open Actions], 'mart_action_center'[priority] = \"P1\")", "#,0", "Governance"),
                    ("Action Value", "SUM('mart_action_center'[action_value])", "$#,0", "Governance"),
                    ("Urgent Critical Actions", "CALCULATE([Open Actions], 'mart_action_center'[priority] IN {\"P0\", \"P1\"}, 'mart_action_center'[due_in_days] <= 2)", "#,0", "Governance"),
                ],
            },
            {
                "name": "mart_ga4_funnel",
                "description": "GA4-style synthetic event funnel prepared for optional live export mapping.",
                "columns": [
                    ("event_date", "dateTime"), ("source", "string"), ("medium", "string"),
                    ("campaign_id", "string"), ("campaign", "string"), ("device_category", "string"),
                    ("sessions", "int64"), ("page_views", "int64"), ("item_views", "int64"),
                    ("add_to_carts", "int64"), ("checkouts", "int64"), ("leads", "int64"),
                    ("purchases", "int64"), ("purchase_revenue", "decimal"),
                ],
                "measures": [
                    ("GA4 Sessions", "SUM('mart_ga4_funnel'[sessions])", "#,0", "GA4 Funnel"),
                    ("GA4 Purchases", "SUM('mart_ga4_funnel'[purchases])", "#,0", "GA4 Funnel"),
                    ("GA4 Purchase Revenue", "SUM('mart_ga4_funnel'[purchase_revenue])", "$#,0", "GA4 Funnel"),
                    ("GA4 Session to Purchase Rate", "DIVIDE([GA4 Purchases], [GA4 Sessions])", "0.00%", "GA4 Funnel"),
                ],
            },
            {
                "name": "mart_marketing_variance_drivers",
                "description": "Month/channel diagnostic drivers without causal claims.",
                "columns": [
                    ("reporting_month", "dateTime"), ("channel_key", "string"), ("channel_name", "string"),
                    ("current_spend", "decimal"), ("prior_spend", "decimal"),
                    ("spend_absolute_variance", "decimal"), ("spend_percentage_variance", "decimal"),
                    ("current_impressions", "int64"), ("prior_impressions", "int64"),
                    ("current_clicks", "int64"), ("prior_clicks", "int64"),
                    ("current_ctr", "decimal"), ("prior_ctr", "decimal"),
                    ("current_cpc", "decimal"), ("prior_cpc", "decimal"),
                    ("current_conversions", "int64"), ("prior_conversions", "int64"),
                    ("current_revenue", "decimal"), ("prior_revenue", "decimal"),
                    ("current_aov", "decimal"), ("prior_aov", "decimal"),
                    ("current_cac", "decimal"), ("prior_cac", "decimal"), ("cac_absolute_variance", "decimal"),
                    ("cac_percentage_variance", "decimal"),
                    ("current_roas", "decimal"), ("prior_roas", "decimal"), ("roas_absolute_variance", "decimal"),
                    ("roas_percentage_variance", "decimal"),
                    ("primary_driver", "string"), ("secondary_driver", "string"), ("severity", "string"),
                    ("recommended_investigation", "string"),
                ],
                "measures": [
                    ("High Variance Drivers", "CALCULATE(COUNTROWS('mart_marketing_variance_drivers'), 'mart_marketing_variance_drivers'[severity] = \"HIGH\")", "#,0", "Diagnostics"),
                    ("ROAS Absolute Variance", "SUM('mart_marketing_variance_drivers'[roas_absolute_variance])", "0.00x", "Diagnostics"),
                ],
            },
            {
                "name": "mart_campaign_action_center",
                "description": "Target-aware deterministic campaign actions with quality overrides.",
                "columns": [
                    ("reporting_month", "dateTime"), ("campaign_id", "string"), ("campaign_name", "string"),
                    ("channel", "string"), ("spend", "decimal"), ("attributed_revenue", "decimal"),
                    ("current_roas", "decimal"), ("current_cac", "decimal"), ("target_roas", "decimal"),
                    ("target_cac", "decimal"), ("performance_status", "string"), ("action_priority", "string"),
                    ("recommended_action", "string"), ("action_reason", "string"),
                    ("supporting_metric", "string"),
                    ("data_quality_status", "string"), ("metric_to_monitor", "string"), ("generated_at", "dateTime"),
                ],
                "measures": [
                    ("Campaign Actions", "COUNTROWS('mart_campaign_action_center')", "#,0", "Campaign Actions"),
                    ("Campaigns to Scale", "CALCULATE([Campaign Actions], 'mart_campaign_action_center'[recommended_action] = \"SCALE\")", "#,0", "Campaign Actions"),
                    ("Data Quality Holds", "CALCULATE([Campaign Actions], 'mart_campaign_action_center'[recommended_action] = \"DATA QUALITY HOLD\")", "#,0", "Campaign Actions"),
                ],
            },
            {
                "name": "mart_budget_scenarios",
                "description": "Deterministic planning simulations for governed baseline, downside, expected, upside, and user-defined assumptions; not causal forecasts or approved budgets.",
                "columns": [
                    ("scenario_name", "string"), ("channel", "string"), ("simulation_status", "string"),
                    ("total_budget", "decimal"), ("channel_allocation", "decimal"), ("channel_budget", "decimal"),
                    ("cpc_assumption", "decimal"), ("conversion_assumption", "decimal"), ("aov_assumption", "decimal"),
                    ("projected_clicks", "decimal"), ("projected_sessions", "decimal"),
                    ("projected_conversions", "decimal"), ("projected_customers", "decimal"),
                    ("projected_revenue", "decimal"), ("projected_cac", "decimal"), ("projected_roas", "decimal"),
                    ("target_roas", "decimal"), ("target_cac", "decimal"),
                    ("roas_target_variance", "decimal"), ("cac_target_variance", "decimal"),
                    ("growth_assumption", "decimal"), ("methodology", "string"),
                ],
                "measures": [
                    ("Scenario Budget", "SUM('mart_budget_scenarios'[channel_budget])", "$#,0", "Scenario Planning"),
                    ("Scenario Projected Revenue", "SUM('mart_budget_scenarios'[projected_revenue])", "$#,0", "Scenario Planning"),
                    ("Scenario Projected Customers", "SUM('mart_budget_scenarios'[projected_customers])", "#,0", "Scenario Planning"),
                    ("Scenario ROAS", "DIVIDE([Scenario Projected Revenue], [Scenario Budget])", "0.00x", "Scenario Planning"),
                    ("Scenario CAC", "DIVIDE([Scenario Budget], [Scenario Projected Customers])", "$#,0", "Scenario Planning"),
                    ("Scenario ROAS Target Variance", "[Scenario ROAS] - MAX('mart_budget_scenarios'[target_roas])", "0.00x", "Scenario Planning"),
                    ("Scenario CAC Target Variance", "[Scenario CAC] - MAX('mart_budget_scenarios'[target_cac])", "$#,0", "Scenario Planning"),
                ],
            },
            {
                "name": "mart_data_product_scorecard",
                "description": "BI data product operating scorecard for reliability, quality, attribution, action ownership, planning readiness, and executive confidence.",
                "columns": [
                    ("scorecard_domain", "string"),
                    ("owner_team", "string"),
                    ("service_level_indicator", "string"),
                    ("current_value", "string"),
                    ("target_value", "string"),
                    ("score", "decimal"),
                    ("score_status", "string"),
                    ("risk_count", "int64"),
                    ("evidence", "string"),
                    ("next_action", "string"),
                    ("dashboard_surface", "string"),
                ],
                "measures": [
                    ("Average Data Product Score", "AVERAGE('mart_data_product_scorecard'[score])", "0.0", "Governance"),
                    ("At Risk Domains", "CALCULATE(COUNTROWS('mart_data_product_scorecard'), 'mart_data_product_scorecard'[score_status] = \"at_risk\")", "#,0", "Governance"),
                    ("Governance Risk Count", "SUM('mart_data_product_scorecard'[risk_count])", "#,0", "Governance"),
                ],
            },
            {
                "name": "mart_semantic_kpi_governance",
                "description": "Certified KPI catalog with definitions, formulas, owners, source marts, dashboard pages, guardrails, dependencies, and refresh SLAs.",
                "columns": [
                    ("kpi_name", "string"),
                    ("business_definition", "string"),
                    ("formula", "string"),
                    ("grain", "string"),
                    ("owner_team", "string"),
                    ("certified_status", "string"),
                    ("source_marts", "string"),
                    ("dashboard_pages", "string"),
                    ("target_or_guardrail", "string"),
                    ("dax_measure_name", "string"),
                    ("quality_dependencies", "string"),
                    ("refresh_sla", "string"),
                    ("interpretation_notes", "string"),
                ],
                "measures": [
                    ("Governed KPIs", "COUNTROWS('mart_semantic_kpi_governance')", "#,0", "Governance"),
                    ("Certified KPIs", "CALCULATE([Governed KPIs], 'mart_semantic_kpi_governance'[certified_status] = \"certified\")", "#,0", "Governance"),
                ],
            },
        ],
        "relationships": [
            ("dim_channel", "channel_key", "mart_channel_performance", "channel_key", "manyToOne"),
            ("dim_channel", "channel_key", "mart_funnel_performance", "channel_key", "manyToOne"),
            ("dim_date", "date_day", "mart_channel_performance", "reporting_month", "manyToOne"),
            ("dim_date", "date_day", "mart_funnel_performance", "reporting_month", "manyToOne"),
            ("dim_date", "date_day", "mart_target_vs_actual", "target_month", "manyToOne"),
            ("dim_date", "date_day", "mart_ga4_funnel", "event_date", "manyToOne"),
            ("dim_campaign", "campaign_id", "mart_ga4_funnel", "campaign_id", "manyToOne"),
            ("dim_channel", "channel_key", "mart_marketing_variance_drivers", "channel_key", "manyToOne"),
            ("dim_campaign", "campaign_id", "mart_campaign_action_center", "campaign_id", "manyToOne"),
        ],
        "dashboard_pages": [
            {
                "page": "Executive Marketing Overview",
                "grain": "Month and channel",
                "business_question": "Are marketing dollars producing efficient revenue and margin?",
                "metrics": ["Total Spend", "Booked Revenue", "Gross Margin", "ROAS", "CAC", "Marketing Efficiency Ratio"],
                "filters": ["Reporting Month", "Channel Group", "Region", "Owner Team"],
            },
            {
                "page": "Channel Performance",
                "grain": "Month, channel, and channel group",
                "business_question": "Which channels are scaling efficiently and which need budget reallocation?",
                "metrics": ["Total Spend", "Total Leads", "Closed Won Conversions", "ROAS", "Cost Per Lead"],
                "filters": ["Reporting Month", "Channel Group", "Device", "Region"],
            },
            {
                "page": "Campaign Intelligence",
                "grain": "Campaign",
                "business_question": "Which campaigns are wasting budget or driving high-value customers?",
                "metrics": ["Campaign Spend", "Attributed Revenue", "Attributed ROAS", "Waste Campaigns"],
                "filters": ["Campaign", "Channel", "Owner Team", "Waste Budget Flag"],
            },
            {
                "page": "Funnel Analysis",
                "grain": "Month and channel",
                "business_question": "Where are leads dropping before revenue conversion?",
                "metrics": ["Funnel Leads", "Funnel MQLs", "Funnel SQLs", "Lead to MQL Rate", "SQL to Close Rate"],
                "filters": ["Reporting Month", "Channel", "Region", "Sales Rep"],
            },
            {
                "page": "Attribution & ROI",
                "grain": "Month, campaign, channel, and attribution model",
                "business_question": "Why do attribution reports disagree across systems?",
                "metrics": ["First Touch Revenue", "Last Touch Revenue", "Linear Revenue", "Time Decay Revenue", "Last vs First Revenue Delta"],
                "filters": ["Reporting Month", "Campaign", "Channel", "Attribution Model"],
            },
            {
                "page": "Target vs Actual",
                "grain": "Month, region, channel, and budget owner",
                "business_question": "Are teams meeting regional budget, lead, and revenue targets?",
                "metrics": ["Target Revenue", "Actual Revenue", "Revenue Attainment", "Target Spend", "Actual Spend", "Spend Attainment"],
                "filters": ["Target Month", "Region", "Channel", "Budget Owner"],
            },
            {
                "page": "Governance & Action Center",
                "grain": "Scorecard domain, KPI, owner team, and action priority",
                "business_question": "Can leaders trust the dashboard, and who owns the next fixes?",
                "metrics": [
                    "Average Data Product Score",
                    "At Risk Domains",
                    "Governance Risk Count",
                    "Open Actions",
                    "P0 Actions",
                    "P1 Actions",
                    "Certified KPIs",
                ],
                "filters": ["Owner Team", "Score Status", "Priority", "Action Type", "Certified Status"],
            },
            {
                "page": "GA4 Funnel",
                "grain": "Date, source, medium, campaign, and device",
                "business_question": "Where does the GA4-style journey drop before purchase?",
                "metrics": ["GA4 Sessions", "GA4 Purchases", "GA4 Purchase Revenue", "GA4 Session to Purchase Rate"],
                "filters": ["Event Date", "Source", "Medium", "Campaign", "Device"],
            },
            {
                "page": "Variance Drivers",
                "grain": "Month and channel",
                "business_question": "Which diagnostic movements contributed to ROAS and CAC change?",
                "metrics": ["High Variance Drivers", "ROAS Absolute Variance"],
                "filters": ["Reporting Month", "Channel", "Severity", "Primary Driver"],
            },
            {
                "page": "Campaign Action Center",
                "grain": "Month and campaign",
                "business_question": "Which transparent actions should marketing leadership prioritize?",
                "metrics": ["Campaign Actions", "Campaigns to Scale", "Data Quality Holds"],
                "filters": ["Reporting Month", "Channel", "Priority", "Recommended Action", "Data Quality Status"],
            },
            {
                "page": "Scenario Planning",
                "grain": "Scenario and channel",
                "business_question": "How do explicit budget, CPC, conversion, AOV, and growth assumptions change planning outcomes?",
                "metrics": ["Scenario Budget", "Scenario Projected Revenue", "Scenario Projected Customers", "Scenario ROAS", "Scenario CAC", "Scenario ROAS Target Variance", "Scenario CAC Target Variance"],
                "filters": ["Scenario Name", "Channel", "Simulation Status"],
            },
        ],
    }


def generate_powerbi_semantic_model() -> dict:
    spec = semantic_model_spec()
    table_dir = OUTPUT_ROOT / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    (OUTPUT_ROOT / "model.tmdl").write_text(build_model_tmdl(spec), encoding="utf-8")
    (OUTPUT_ROOT / "relationships.tmdl").write_text(build_relationships_tmdl(spec), encoding="utf-8")
    (OUTPUT_ROOT / "dashboard_pages.yml").write_text(
        yaml.safe_dump({"dashboard_pages": spec["dashboard_pages"]}, sort_keys=False),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "semantic_model_manifest.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_name": spec["model_name"],
                "table_count": len(spec["tables"]),
                "measure_count": sum(len(table.get("measures", [])) for table in spec["tables"]),
                "relationship_count": len(spec["relationships"]),
                "dashboard_page_count": len(spec["dashboard_pages"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    for table in spec["tables"]:
        (table_dir / f"{slugify(table['name'])}.tmdl").write_text(build_table_tmdl(table), encoding="utf-8")

    (OUTPUT_ROOT / "README.md").write_text(build_readme(spec), encoding="utf-8")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_folder": str(OUTPUT_ROOT.relative_to(PROJECT_ROOT)),
        "tables": [table["name"] for table in spec["tables"]],
        "measure_count": sum(len(table.get("measures", [])) for table in spec["tables"]),
    }


def build_model_tmdl(spec: dict) -> str:
    lines = [
        f"model '{spec['model_name']}'",
        f"\tcompatibilityLevel: {spec['compatibility_level']}",
        "\tculture: en-US",
        "\tdiscourageImplicitMeasures",
        "\tannotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "\tannotation SemanticPackagePurpose = \"Power BI-ready semantic package for the marketing warehouse\"",
    ]
    return "\n".join(lines) + "\n"


def build_relationships_tmdl(spec: dict) -> str:
    lines = ["// Power BI TMDL-style relationship definitions"]
    for from_table, from_col, to_table, to_col, cardinality in spec["relationships"]:
        rel_name = f"{from_table}_{from_col}_to_{to_table}_{to_col}"
        lines.extend(
            [
                f"relationship {rel_name}",
                f"\tfromColumn: '{to_table}'[{to_col}]",
                f"\ttoColumn: '{from_table}'[{from_col}]",
                f"\tcardinality: {cardinality}",
                "\tcrossFilteringBehavior: oneDirection",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_table_tmdl(table: dict) -> str:
    hidden = set(table.get("hidden_columns", []))
    lines = [
        f"table '{table['name']}'",
        f"\tdescription: \"{table['description']}\"",
        "\tlineageTag: " + slugify(table["name"]),
        "",
    ]
    for column_name, data_type in table["columns"]:
        lines.extend(
            [
                f"\tcolumn {column_name}",
                f"\t\tdataType: {data_type}",
                "\t\tsummarizeBy: none",
            ]
        )
        if column_name in hidden:
            lines.append("\t\tisHidden")
        lines.append("")
    for measure_name, expression, format_string, folder in table.get("measures", []):
        lines.extend(
            [
                f"\tmeasure '{measure_name}' = {expression}",
                f"\t\tformatString: \"{format_string}\"",
                f"\t\tdisplayFolder: \"{folder}\"",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_readme(spec: dict) -> str:
    page_lines = []
    for page in spec["dashboard_pages"]:
        page_lines.append(f"- **{page['page']}**: {page['business_question']}")
    return (
        "# Power BI Semantic Model Package\n\n"
        "This folder contains TMDL-style semantic-model assets for the marketing ETL warehouse. "
        "It is designed as a source-controlled blueprint for importing exported warehouse tables into Power BI, "
        "setting relationships, organizing measures, and building dashboard pages.\n\n"
        "Generated files:\n"
        "- `model.tmdl`: model-level settings.\n"
        "- `relationships.tmdl`: star-schema relationship definitions.\n"
        "- `roles.tmdl`: Executive, Channel Manager, and Regional Manager role design; runtime enforcement requires Power BI Desktop or Service validation.\n"
        "- `tables/*.tmdl`: table, column, and measure definitions.\n"
        "- `dashboard_pages.yml`: dashboard page blueprint.\n"
        "- `semantic_model_manifest.json`: generated asset counts.\n\n"
        "Dashboard pages:\n"
        + "\n".join(page_lines)
        + "\n"
    )


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def main() -> None:
    print(json.dumps(generate_powerbi_semantic_model(), indent=2))


if __name__ == "__main__":
    main()
