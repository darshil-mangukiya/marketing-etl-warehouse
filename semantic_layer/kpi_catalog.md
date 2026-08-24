# KPI Definition Catalog

## Executive KPIs

| KPI | Definition | Primary Mart |
|---|---|---|
| Spend | Sum of paid media cost. | `mart_channel_performance`, `mart_campaign_performance` |
| Booked Revenue | Sum of sales conversion deal value. | `mart_channel_performance`, `mart_customer_value` |
| Gross Margin | Sum of conversion gross margin. | `mart_channel_performance`, `mart_budget_efficiency` |
| ROAS | Booked revenue divided by spend. | `mart_channel_performance` |
| MER | Gross margin divided by spend. | `mart_channel_performance` |
| CAC | Spend divided by closed-won conversions. | `mart_channel_performance` |
| LTV | Customer lifetime revenue. | `mart_customer_value` |
| Funnel Conversion Rate | Stage count divided by prior stage count. | `mart_funnel_performance` |
| Target Attainment | Actual metric divided by target metric. | `mart_target_vs_actual` |
| Budget Efficiency | Contribution after marketing and recommendation category. | `mart_budget_efficiency` |
| Data Product Score | Operating-health score for reliability, quality, attribution, action management, planning readiness, and executive confidence. | `mart_data_product_scorecard` |
| Open Critical Actions | Count of P0/P1 actions requiring owner-team follow-up. | `mart_action_center` |
| Attribution Coverage | Share of measurable lead and conversion records with usable attribution identifiers. | `mart_journey_quality` |
| Forecast ROAS | Forecast booked revenue divided by forecast spend for the next planning horizon. | `mart_performance_forecast` |

## Metric Rules

- Spend is sourced from platform spend fields and coalesced to zero only after validation captures null-spend defects.
- Revenue is sourced from sales conversions, not platform-reported conversions.
- Attribution revenue supports first-touch, last-touch, and linear views.
- CAC should be filtered to paid channels for executive reporting.
- LTV should be analyzed by acquisition channel and customer segment.
- Target attainment must be scoped to month, region, and channel.
- Executive-facing dashboard releases should reference the KPI governance mart for owner, formula, grain, guardrail, and quality dependency.
- Data Product Score is an operating control, not a business-growth KPI; use it to decide whether a dashboard is publish-ready.
