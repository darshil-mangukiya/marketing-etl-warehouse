# Row Count Summary

This page documents the generated source-data volume currently present in the repository and the configured scale profile. Local smoke mode intentionally uses smaller row counts so the pipeline can run quickly on a laptop.

## Current Generated Source Batch

| Field | Value |
|---|---|
| Manifest | `data_sources/generated/manifest.json` |
| Batch ID | `batch_20260517T220817Z` |
| Profile | `smoke` |
| Generated at | `2026-05-17T22:08:17.912641+00:00` |
| Generated files | 16 |
| Generated source rows | 11,052 |
| Formats | CSV, JSONL, Parquet |

## Source Row Counts

| Source/System | Table or File Pattern | Current Generated Rows | Expected Scale Profile | Notes |
|---|---|---:|---:|---|
| Google Ads | `data_sources/generated/source_system=google_ads/.../*.jsonl` | 2,510 | 5,000,000 | Paid media campaign metrics in JSONL |
| Facebook Ads | `data_sources/generated/source_system=facebook_ads/.../*.csv` | 1,807 | 3,000,000 | Paid social campaign and ad group metrics |
| TikTok Ads | `data_sources/generated/source_system=tiktok_ads/.../*.parquet` | 1,205 | 2,000,000 | Short-form social campaign metrics |
| Website Analytics | `data_sources/generated/source_system=website_analytics/.../*.parquet` | 3,000 | 10,000,000 | Session, device, geography, and source data |
| CRM Leads | `data_sources/generated/source_system=crm_leads/.../*.csv` | 1,300 | 2,000,000 | Lead source and qualification-stage data |
| Sales Conversions | `data_sources/generated/source_system=sales_conversions/.../*.jsonl` | 600 | 1,000,000 | Converted leads, revenue, products, and lag |
| Marketing Targets | `data_sources/generated/source_system=marketing_targets/.../*.csv` | 120 | 5,000 | Monthly and regional targets |
| Campaign Mapping | `data_sources/generated/source_system=campaign_mapping/.../*.csv` | 500 | Reference scale | Campaign normalization map |
| Region Mapping | `data_sources/generated/source_system=region_mapping/.../*.csv` | 10 | Reference scale | Region normalization map |

## Ingestion Summary

| Source/System | Files | Rows | Accepted | Rejected | Failed |
|---|---:|---:|---:|---:|---:|
| Google Ads | 3 | 2,510 | 2,487 | 23 | 0 |
| Facebook Ads | 2 | 1,807 | 1,791 | 16 | 0 |
| TikTok Ads | 2 | 1,205 | 1,201 | 4 | 0 |
| Website Analytics | 3 | 3,000 | 3,000 | 0 | 0 |
| CRM Leads | 2 | 1,300 | 1,300 | 0 | 0 |
| Sales Conversions | 1 | 600 | 600 | 0 | 0 |
| Marketing Targets | 1 | 120 | 120 | 0 | 0 |
| Campaign Mapping | 1 | 500 | 500 | 0 | 0 |
| Region Mapping | 1 | 10 | 10 | 0 | 0 |

Source: `data/logs/latest_ingestion_summary.json`.

## Demo Mart Row Counts

The generated demo mart manifest is stored at `data/exports/demo_mart_manifest.json`. It currently includes 28 reporting and monitoring exports, including:

| Mart | Rows | File |
|---|---:|---|
| `mart_campaign_performance` | 250 | `data/exports/demo_mart_campaign_performance.csv` |
| `mart_campaign_optimization` | 250 | `data/exports/demo_mart_campaign_optimization.csv` |
| `mart_customer_value` | 600 | `data/exports/demo_mart_customer_value.csv` |
| `mart_target_vs_actual` | 120 | `data/exports/demo_mart_target_vs_actual.csv` |
| `mart_channel_performance` | 11 | `data/exports/demo_mart_channel_performance.csv` |
| `mart_data_quality_monitoring` | 16 | `data/exports/demo_mart_data_quality_monitoring.csv` |
| `mart_source_health` | 9 | `data/exports/demo_mart_source_health.csv` |

## Scale Notes

- `smoke` profile is used for quick local validation.
- `dev` profile increases row counts for local development.
- `scale_test` profile defines the project's large-volume target and is documented in `data_sources/config/source_volume.yml`.
- Tie scale-test volume references to an executed run and matching manifest.
