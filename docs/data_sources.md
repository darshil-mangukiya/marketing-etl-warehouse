# Data Sources

The local pipeline generates marketing, web, CRM, sales, target, and reference records. The generator includes operational issues that a warehouse pipeline must handle: inconsistent campaign names, duplicate IDs, missing attribution IDs, null spend, late-arriving conversions, schema drift, and regional variation.

## Source Inventory

| Source | System Type | Format | Primary Grain | Key Fields |
|---|---|---|---|---|
| Google Ads | Paid media API-style feed | JSONL | campaign / ad group / date | campaign ID, ad group ID, spend, impressions, clicks, conversions |
| Facebook Ads | Paid media API-style feed | CSV | campaign / ad set / date | campaign ID, ad set ID, spend, reach, clicks, conversions |
| TikTok Ads | Paid media API-style feed | Parquet | campaign / creative / date | campaign ID, creative ID, spend, views, clicks, conversions |
| Website Analytics | Web analytics event/session feed | Parquet | session | session ID, customer ID, device, geography, source, bounce flag |
| CRM Leads | CRM lead feed | CSV | lead | lead ID, customer ID, lead source, qualification stage, assigned rep |
| Sales Conversions | Sales event feed | JSONL | conversion/deal | conversion ID, lead ID, deal value, product, close date |
| Marketing Targets | Planning feed | CSV | month / region / channel | target month, region, channel, target revenue, budget |
| Campaign Mapping | Reference mapping | CSV | campaign | campaign ID, normalized campaign, channel, product, region |
| Region Mapping | Reference mapping | CSV | region | region code, region name, country |

## File Layout

Generated source data is written under:

```text
data_sources/generated/
  source_system=<source>/
    batch_id=<batch>/
      <source>_part_00000.<format>
```

Ingested files are copied into the local lake under:

```text
data/lake/raw/
  source_system=<source>/
    load_date=<date>/
      batch_id=<batch>/
```

## Current Smoke Evidence

The current smoke profile is documented in `docs/row_count_summary.md`.

| Source | Current Smoke Rows | Scale Profile Rows |
|---|---:|---:|
| Google Ads | 2,510 | 5,000,000 |
| Facebook Ads | 1,807 | 3,000,000 |
| TikTok Ads | 1,205 | 2,000,000 |
| Website Analytics | 3,000 | 10,000,000 |
| CRM Leads | 1,300 | 2,000,000 |
| Sales Conversions | 600 | 1,000,000 |
| Marketing Targets | 120 | 5,000 |
| Campaign Mapping | 500 | configured reference volume |
| Region Mapping | 10 | configured reference volume |

## Data Issues Simulated

- duplicate campaign IDs and lead IDs
- inconsistent campaign naming across platforms
- missing attribution identifiers
- null and invalid spend records
- impossible click/impression relationships
- late-arriving conversions
- schema drift in source files
- unmapped regions or campaigns
- channel naming inconsistencies
- seasonal demand and budget variation

These issues feed the validation framework, rejected-record outputs, warehouse normalization logic, attribution marts, and monitoring views.
