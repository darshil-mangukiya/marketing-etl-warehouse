# Power BI Setup Guide

This guide explains how to use the exported marts and semantic assets to build a Power BI report for the Campaign ROI Reporting Automation & Marketing Performance Analytics Platform.

For review or rebuild work, use the self-contained handoff package in `data/exports/powerbi_handoff/`: import-ready CSV tables, `dax_measures.md`, `relationships.md`, page specs, Power Query notes, and screenshot checklist. The `dashboards/powerbi/` folder keeps the completed Desktop report and source-controlled semantic assets used to generate that handoff.

## Import The Exported Tables

Use the generated CSV exports in `data/exports/powerbi_handoff/` as Power BI import sources.

Recommended tables:

- `dim_date.csv`
- `dim_campaign.csv`
- `dim_channel.csv`
- `dim_region.csv`
- `dim_device.csv`
- `dim_customer_segment.csv`
- `fact_campaign_performance.csv`
- `fact_ad_spend.csv`
- `fact_leads.csv`
- `fact_conversions.csv`
- `fact_revenue_attribution.csv`
- `fact_budget_targets.csv`
- `mart_campaign_action_recommendations.csv`

For a more warehouse-style model, use the dbt facts and dimensions from PostgreSQL or generate fact/dimension exports before importing.

## Suggested Relationships

If importing fact and dimension tables, use these relationship patterns:

| From | To | Relationship |
|---|---|---|
| `fact_campaign_performance.campaign_key` | `dim_campaign.campaign_key` | many-to-one |
| `fact_campaign_performance.channel_key` | `dim_channel.channel_key` | many-to-one |
| `fact_campaign_performance.date_key` | `dim_date.date_key` | many-to-one |
| `fact_campaign_performance.region_key` | `dim_region.region_key` | many-to-one |
| `fact_campaign_performance.device_key` | `dim_device.device_key` | many-to-one |
| `fact_leads.customer_key` | `dim_customer.customer_key` | many-to-one |
| `fact_revenue.product_key` | `dim_product.product_key` | many-to-one |
| `fact_attribution.source_system_key` | `dim_source_system.source_system_key` | many-to-one |

Keep filter direction single by default. Use bidirectional filters only when a specific report interaction requires it and the ambiguity is understood.

## Apply DAX Measures

Use `data/exports/powerbi_handoff/dax_measures.md` as the measure source. Create a dedicated Power BI measure table, then add measures such as:

- Total Spend
- Total Revenue
- ROAS
- CAC
- Conversion Rate
- Target Attainment %
- Budget Variance
- Attributed Revenue
- Average Conversion Lag
- Data Quality Failure Rate

Validate each measure against the exported mart values before using the dashboard for review.

## Recommended Dashboard Pages

| Page | Purpose |
|---|---|
| Executive Overview | Spend, revenue, ROAS, CAC, LTV, target attainment, source health |
| Channel Performance | Compare spend, leads, conversions, revenue, and ROAS by channel |
| Campaign Intelligence | Identify campaigns to scale, fix, or pause |
| Funnel Analysis | Show session-to-lead-to-opportunity-to-closed-won drop-off |
| Attribution and ROI | Compare first-touch, last-touch, and attributed revenue views |
| Target vs Actual | Track budget, pipeline, and revenue attainment by month/region |
| Data Quality and Monitoring | Show freshness, rejected rows, mapping gaps, and source health |

## Validation Checklist

- [ ] Imported tables refresh without file path errors.
- [ ] Date columns are typed as date or datetime.
- [ ] Currency fields are numeric.
- [ ] Relationship cardinality is correct.
- [ ] DAX measures match mart totals.
- [ ] Slicers filter the expected pages.
- [ ] No dashboard page uses undefined business logic.
- [ ] Data-quality caveats are visible where needed.
- [ ] Data provenance is included in report notes.

## Screenshots

Completed report captures are stored in `evidence/screenshots/powerbi/`. Refresh these after changing the `.pbix`:

- `evidence/screenshots/powerbi/executive_overview.png`
- `evidence/screenshots/powerbi/channel_performance.png`
- `evidence/screenshots/powerbi/campaign_roi.png`
- `evidence/screenshots/powerbi/funnel_analysis.png`
- `evidence/screenshots/powerbi/attribution_model_comparison.png`
- `evidence/screenshots/powerbi/target_vs_actual.png`
- `evidence/screenshots/powerbi/data_quality_source_health.png`

## PBIP And TMDL Assets

Existing semantic scaffolds:

- `semantic_layer/powerbi_pbip/MarketingPlatform.pbip`
- `semantic_layer/powerbi_pbip/README.md`
- `semantic_layer/powerbi_tmdl/model.tmdl`
- `semantic_layer/powerbi_tmdl/relationships.tmdl`
- `semantic_layer/powerbi_tmdl/dashboard_pages.yml`
- `semantic_layer/powerbi_tmdl/semantic_model_manifest.json`

The current semantic manifest records 17 semantic tables, 59 DAX measures, 9 TMDL relationships, and 11 page specifications. The completed physical PBIX contains seven report pages.

## Project Scope

- The completed dashboard is committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix` with page captures in `evidence/screenshots/powerbi/`; refresh screenshots after editing the report.
- File paths may need to be updated after cloning the repository.
- Some generated mart exports are denormalized for dashboard speed, while the warehouse model uses facts and dimensions.
- Locally generated data keeps the report reproducible without customer records.
