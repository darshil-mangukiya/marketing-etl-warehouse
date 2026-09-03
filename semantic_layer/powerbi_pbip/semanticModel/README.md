# Semantic Model Notes

Use the generated TMDL-style package in `semantic_layer/powerbi_tmdl/` as the source of truth.

Required tables:

- `mart_channel_performance`
- `mart_campaign_performance`
- `mart_funnel_performance`
- `mart_target_vs_actual`
- `mart_attribution_model_comparison`
- `mart_action_center`
- `mart_data_product_scorecard`
- `mart_semantic_kpi_governance`
- `dim_date`
- `dim_channel`
- `dim_campaign`
- `dim_customer`
- `dim_region`

Recommended conventions:

- Hide surrogate key columns from report users.
- Keep ratios as measures, not calculated columns.
- Certify executive KPIs only after the governance packet passes.
- Put quality, source health, and action-center measures in a Governance display folder.
- Use aggregated or masked tables for leadership pages.
