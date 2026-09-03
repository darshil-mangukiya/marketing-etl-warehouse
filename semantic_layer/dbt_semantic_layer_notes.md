# dbt Semantic Layer Notes

The dbt project includes semantic models, governed metrics, and dashboard exposures in `dbt/models/marts/semantic_layer.yml`.

## Semantic Models

- `channel_performance_semantic`: spend, revenue, margin, ROAS, CAC, CTR, and channel efficiency.
- `funnel_performance_semantic`: lead, MQL, SQL, and conversion-stage movement.
- `target_attainment_semantic`: budget, lead, conversion, and revenue target tracking.

## Governed Metrics

- Total Spend
- Booked Revenue
- Gross Margin
- ROAS
- Marketing Efficiency Ratio
- CTR
- Cost per Lead
- CAC
- Lead to MQL Rate
- Revenue Attainment

## Exposures

- Executive Marketing Overview
- Campaign Intelligence
- Data Quality and Monitoring

These exposures connect BI dashboards back to dbt marts so dashboard ownership, upstream dependencies, and metric definitions are explicit.
