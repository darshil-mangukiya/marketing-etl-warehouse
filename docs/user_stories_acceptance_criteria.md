# User Stories and Acceptance Criteria

| User Story | Business Priority | Data Source | KPI/Mart Used | Acceptance Criteria | Validation Method |
|---|---|---|---|---|---|
| As a CMO, I want to compare ROAS and CAC by channel so I can reallocate budget toward profitable channels. | High | Paid media, sales conversions, targets | `mart_channel_performance` | ROAS and CAC formulas match KPI catalog; filters work by month, channel, and region; totals reconcile to exported mart. | Compare dashboard values to `data/exports/demo_mart_channel_performance.csv`. |
| As a Growth Marketing Manager, I want to identify campaigns with high spend and low conversion rate so I can pause or optimize wasted spend. | High | Google Ads, Facebook Ads, TikTok Ads, attribution data | `mart_campaign_performance`, `mart_campaign_optimization` | Campaigns show spend, conversions, attributed ROAS, waste flag, and recommended action; missing campaign mappings are visible. | Review campaign mart totals and waste flags in export package. |
| As a Sales Operations Manager, I want to see lead stage conversion by source so I can improve lead handoff quality. | High | Website analytics, CRM leads, sales conversions | `mart_funnel_performance` | Funnel stages include leads, MQLs, SQLs, and conversions; rates are calculated from prior stage counts; channel filters work. | Reconcile funnel rates to `mart_funnel_performance`. |
| As a Finance Manager, I want target vs actual spend and revenue tracking so I can monitor monthly pacing. | High | Marketing targets, campaign spend, sales conversions | `mart_target_vs_actual`, `mart_budget_pacing` | Target and actual metrics are shown by month, region/channel, and budget owner; variance and attainment fields are available. | Compare exported target and budget pacing files. |
| As a BI Developer, I want governed KPI definitions and relationship guidance so dashboard metrics stay consistent. | High | Semantic layer, marts | KPI catalog, DAX catalog, relationship map | KPI formulas match catalog; relationships use documented keys; undefined business logic is not used. | Review `semantic_layer/kpi_catalog.md`, DAX catalog, and Power BI setup guide. |
| As a Data Engineer, I want source freshness and rejected-record status so I can detect ingestion issues before reporting. | High | Ingestion logs, validation outputs | `mart_source_health`, `mart_data_quality_monitoring` | Source health shows row counts, acceptance rates, rejected rows, and watermark status; failed rules include source and file context. | Review observability output and quality marts. |
| As an Analytics Engineer, I want dbt marts with clear grain and tests so downstream reporting is reusable. | Medium | PostgreSQL raw data, dbt models | core facts/dimensions, reporting marts | Fact/mart grain is documented; custom dbt tests cover attribution, KPI relationships, and mart grain. | Review `docs/warehouse_model.md`, `dbt/tests/`, and release tests. |
| As Executive Leadership, I want an exception-based overview so I can focus on performance and data quality risks. | Medium | Reporting marts, quality marts | executive scorecard, action center, governance packet | Executive status, open actions, quality alerts, and source health are visible; stale or low-quality sources are not hidden. | Review generated executive and governance reports. |

## General Acceptance Rules

- KPI formulas must match `semantic_layer/kpi_catalog.md`.
- Date, channel, region, campaign, device, and attribution filters must apply where each mart contains those fields.
- Records with missing attribution should be flagged or visible through quality/journey outputs.
- Dashboard output should reconcile to mart totals before signoff.
- Data freshness status should be visible before executive reporting.
- Rejected rows should be documented with source, file, rule, severity, and batch context.

