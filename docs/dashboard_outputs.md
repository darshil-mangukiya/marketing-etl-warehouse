# Dashboard Outputs

This document describes the reporting outputs supported by the warehouse marts and semantic layer.

## Dashboard Pages

| Page | Primary KPIs | Business Question |
|---|---|---|
| Executive Overview | spend, revenue, ROAS, CAC, target attainment | Is marketing performance on plan? |
| Channel Performance | spend, clicks, leads, conversions, ROAS | Which channels should receive more or less budget? |
| Campaign Intelligence | ROI, wasted spend, mapping status, conversion lag | Which campaigns should be scaled, fixed, or paused? |
| Funnel Analysis | session-to-lead, MQL rate, SQL rate, win rate | Where are leads dropping from the funnel? |
| Attribution and ROI | first touch, last touch, attributed revenue | Which touchpoints and channels influence revenue? |
| Target vs Actual | target, actual, variance, pacing | Are teams meeting monthly and regional goals? |
| Budget Efficiency | budget, spend, variance, pacing status | Where is spend over or under plan? |
| Customer Value | customer value, margin, product mix, segment | Which channels produce higher-value customers? |
| Data Quality and Monitoring | freshness, rejected rows, missing mappings, source health | Can the reporting data be trusted? |

## Reporting Marts

| Mart | Purpose |
|---|---|
| `mart_channel_performance` | Channel-level spend, revenue, ROAS, CAC, and conversion performance |
| `mart_campaign_performance` | Campaign-level profitability, engagement, and mapping status |
| `mart_funnel_performance` | Session, lead, MQL, SQL, and closed-won funnel progression |
| `mart_attribution_summary` | First-touch, last-touch, and attributed revenue summaries |
| `mart_target_vs_actual` | Target attainment by month, region, and channel |
| `mart_budget_efficiency` | Budget variance, pacing, and spend efficiency |
| `mart_customer_value` | Customer value and LTV-ready aggregation prep |
| `mart_data_quality_monitoring` | Validation outcomes, rejected records, and quality status |
| `mart_source_health` | Source freshness, row counts, and operational status |
| `mart_action_center` | Recommended operational follow-up for quality and performance issues |

## Recommended Filters

- date range
- channel
- campaign
- region
- device
- product
- sales rep
- lead stage
- attribution model
- source system

## Drilldown Paths

| Starting View | Drilldown |
|---|---|
| Channel Performance | channel to campaign to region/device |
| Campaign Intelligence | campaign to ad group/source record |
| Funnel Analysis | funnel stage to campaign/source |
| Attribution and ROI | model to touchpoint to conversion |
| Target vs Actual | region to channel to campaign |
| Data Quality | source system to rule to rejected rows |

## Output Assets

- Streamlit app: `bi_app/streamlit_app.py`
- Power BI dashboard (7 pages): `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`
- Power BI dashboard data: `dashboards/powerbi/data/` (13 CSV tables)
- Power BI dashboard screenshots: `evidence/screenshots/powerbi/`
- Exported marts: `data/exports/demo_mart_*.csv`
- KPI catalog: `semantic_layer/kpi_catalog.md`
- DAX measure catalog: `semantic_layer/dax_measure_catalog.md`
- Relationship map: `semantic_layer/star_schema_relationship_map.md`
- Dashboard measure matrix: `semantic_layer/dashboard_measure_matrix.md`
- Power BI setup guide: `semantic_layer/powerbi/POWERBI_SETUP_GUIDE.md`
- TMDL package: `semantic_layer/powerbi_tmdl/`
- PBIP scaffold: `semantic_layer/powerbi_pbip/`

## Generated Preview Evidence

- `evidence/generated/dashboard_wireframe.svg`
- `evidence/generated/dashboard_executive_preview.svg`
- `evidence/generated/dashboard_governance_preview.svg`
- `evidence/generated/dashboard_observability_preview.svg`
