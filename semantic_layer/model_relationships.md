# Power BI Relationship Map

## Recommended Import Tables

Facts and marts:

- `fact_campaign_performance`
- `fact_sessions`
- `fact_leads`
- `fact_conversions`
- `fact_revenue`
- `fact_targets`
- `fact_attribution`
- `mart_channel_performance`
- `mart_campaign_performance`
- `mart_funnel_performance`
- `mart_target_vs_actual`
- `mart_attribution_summary`
- `mart_customer_value`
- `mart_budget_efficiency`
- `mart_data_quality_monitoring`

Dimensions:

- `dim_date`
- `dim_campaign`
- `dim_channel`
- `dim_customer`
- `dim_region`
- `dim_device`
- `dim_product`
- `dim_sales_rep`
- `dim_source_system`

## Core Relationships

| From | To | Cardinality | Direction |
|---|---|---|---|
| `dim_date[date_actual]` | `fact_campaign_performance[event_date]` | 1:* | Single |
| `dim_campaign[campaign_key]` | `fact_campaign_performance[campaign_key]` | 1:* | Single |
| `dim_channel[channel_key]` | `fact_campaign_performance[channel_key]` | 1:* | Single |
| `dim_region[region_key]` | `fact_campaign_performance[region_key]` | 1:* | Single |
| `dim_device[device_key]` | `fact_sessions[device_key]` | 1:* | Single |
| `dim_customer[customer_key]` | `fact_leads[customer_key]` | 1:* | Single |
| `dim_customer[customer_key]` | `fact_conversions[customer_key]` | 1:* | Single |
| `dim_product[product_key]` | `fact_conversions[product_key]` | 1:* | Single |
| `dim_campaign[campaign_key]` | `fact_attribution[campaign_key]` | 1:* | Single |

## Modeling Guidance

- Use warehouse facts for drill-through and marts for dashboard landing pages.
- Keep relationships single-direction unless a specific drill path requires bidirectional filtering.
- Use `dim_date` as the single date table and create inactive relationships for alternate date roles when needed.
- Do not relate marts to facts directly; marts are aggregate presentation tables.
