# DAX Measure Catalog

```DAX
Total Spend = SUM('mart_channel_performance'[spend])

Booked Revenue = SUM('mart_channel_performance'[booked_revenue])

Gross Margin = SUM('mart_channel_performance'[gross_margin])

ROAS = DIVIDE([Booked Revenue], [Total Spend])

MER = DIVIDE([Gross Margin], [Total Spend])

Clicks = SUM('mart_channel_performance'[clicks])

Impressions = SUM('mart_channel_performance'[impressions])

CTR = DIVIDE([Clicks], [Impressions])

CPC = DIVIDE([Total Spend], [Clicks])

Leads = SUM('mart_channel_performance'[leads])

Qualified Leads = SUM('mart_channel_performance'[qualified_leads])

Cost per Lead = DIVIDE([Total Spend], [Leads])

Closed Won Conversions = SUM('mart_channel_performance'[closed_won_conversions])

CAC = DIVIDE([Total Spend], [Closed Won Conversions])

Lead to MQL Rate = DIVIDE(SUM('mart_funnel_performance'[mqls]), SUM('mart_funnel_performance'[total_leads]))

MQL to SQL Rate = DIVIDE(SUM('mart_funnel_performance'[sales_qualified_leads]), SUM('mart_funnel_performance'[mqls]))

SQL to Close Rate = DIVIDE(SUM('mart_funnel_performance'[conversions]), SUM('mart_funnel_performance'[sales_qualified_leads]))

Revenue Attainment = DIVIDE(SUM('mart_target_vs_actual'[actual_revenue]), SUM('mart_target_vs_actual'[target_revenue]))

Spend Attainment = DIVIDE(SUM('mart_target_vs_actual'[actual_spend]), SUM('mart_target_vs_actual'[target_spend]))

Contribution After Marketing = SUM('mart_budget_efficiency'[contribution_after_marketing])

Attributed Revenue = SUM('mart_attribution_summary'[attributed_revenue])

Weighted Conversions = SUM('mart_attribution_summary'[weighted_conversions])

Data Quality Failures = SUM('mart_data_quality_monitoring'[failed_count])
```

## Power BI Notes

- Set date tables using `dim_date[date_actual]`.
- Mark `mart_channel_performance[reporting_month]` and other month fields as date fields.
- Use slicers for channel, region, campaign, product, attribution model, and customer segment.
- Hide technical keys unless needed for drill-through.
