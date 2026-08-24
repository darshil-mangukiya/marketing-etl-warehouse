# Superset Optional BI Scaffold

This folder documents how the marts can be connected to Apache Superset.

## Recommended Datasets

- `mart.mart_channel_performance`
- `mart.mart_campaign_performance`
- `mart.mart_funnel_performance`
- `mart.mart_target_vs_actual`
- `mart.mart_attribution_summary`
- `mart.mart_customer_value`
- `mart.mart_budget_efficiency`
- `mart.mart_data_quality_monitoring`

## Chart Mapping

| Dashboard Page | Superset Chart Type | Dataset |
|---|---|---|
| Executive Overview | Big Number + Time Series Line | `mart_channel_performance` |
| Channel Performance | Bubble Chart + Bar Chart | `mart_channel_performance` |
| Campaign Intelligence | Table + Bar Chart | `mart_campaign_performance` |
| Funnel Analysis | Funnel/Bar Chart | `mart_funnel_performance` |
| Attribution and ROI | Grouped Bar Chart | `mart_attribution_summary` |
| Target vs Actual | Scatter + KPI Cards | `mart_target_vs_actual` |
| Data Quality Monitoring | Status Table + Bar Chart | `mart_data_quality_monitoring` |

## Connection

Use the PostgreSQL SQLAlchemy URI from `.env`:

```text
postgresql+psycopg2://marketing:marketing@postgres:5432/marketing_warehouse
```
