# Requirement Traceability Matrix

| Business question | KPI catalog key | Source/mart | Dashboard page | UAT scenario |
|---|---|---|---|---|
| Which campaigns produce ROI? | campaign_roi | mart_campaign_performance | Campaign ROI Deep Dive | 5 |
| Which channels are efficient? | roas, cac | mart_channel_performance | Channel Performance | 1, 6 |
| Where is the funnel leaking? | lead_to_mql_rate, sql_to_close_rate | mart_funnel_performance | Funnel Conversion | 4 |
| Are targets on track? | revenue_attainment, spend_attainment | mart_target_vs_actual | Budget Pacing & Targets | 7 |
| Why do attribution reports disagree? | attributed_revenue | mart_attribution_model_comparison | Attribution & Customer Value | 8 |
| Can leaders trust the data? | data_product_score | mart_data_product_scorecard, mart_source_health | Data Quality & Refresh Health | 9, 10 |
| Which campaigns should be scaled or paused? | campaign_roi, roas | campaign_action_recommendations | Campaign ROI Deep Dive | 5, 11 |
| Which sources have quality issues? | data_product_score | mart_source_health, mart_data_quality_monitoring | Data Quality & Refresh Health | 9, 10 |
