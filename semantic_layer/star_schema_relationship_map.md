# Star Schema Relationship Map

The reporting model is intentionally BI-friendly: conformed dimensions sit around atomic facts and curated marts. Hidden surrogate keys support relationships while dashboard authors work with business labels.

## Core Warehouse Relationships

| Dimension | Key | Fact | Key | Cardinality | Reporting Purpose |
|---|---:|---|---:|---|---|
| `dim_campaign` | `campaign_key` | `fact_campaign_performance` | `campaign_key` | 1:* | Campaign spend, clicks, conversions, and attributed revenue |
| `dim_campaign` | `campaign_key` | `fact_conversions` | `campaign_key` | 1:* | Campaign-to-sales conversion linkage |
| `dim_campaign` | `campaign_key` | `fact_revenue` | `campaign_key` | 1:* | Revenue and gross margin by acquisition campaign |
| `dim_channel` | `channel_key` | `fact_campaign_performance` | `channel_key` | 1:* | Paid search/social and channel group reporting |
| `dim_channel` | `channel_key` | `fact_leads` | `channel_key` | 1:* | Lead funnel movement by channel |
| `dim_region` | `region_key` | `fact_campaign_performance` | `region_key` | 1:* | Regional spend and performance |
| `dim_customer` | `customer_key` | `fact_conversions` | `customer_key` | 1:* | LTV and customer acquisition analysis |
| `dim_product` | `product_key` | `fact_revenue` | `product_key` | 1:* | Revenue by purchased product |
| `dim_device` | `device_key` | `fact_sessions` | `device_key` | 1:* | Device-level session and conversion analysis |

## Power BI Defaults

- Use single-direction filtering from dimensions to facts and marts.
- Hide `*_key`, ingestion metadata, hashes, and technical flags from report view.
- Mark `dim_date[date_day]` as the date table.
- Prefer curated marts for executive pages and atomic facts for analyst drillthrough.
- Keep attribution model comparisons on a dedicated page so attribution assumptions are explicit.
