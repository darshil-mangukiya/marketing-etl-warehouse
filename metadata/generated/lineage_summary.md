# Lineage Metadata Export

This export translates the local dbt/catalog graph into OpenLineage-style run events and DataHub-style metadata change events. It is intentionally dependency-free so it can be generated during local demos without a running metadata platform.

- OpenLineage events: `45`
- DataHub metadata events: `48`
- Sources: `13`
- Warehouse models: `17`
- Reporting models: `13`

Critical marts represented in lineage:
- `mart_channel_performance`
- `mart_campaign_performance`
- `mart_funnel_performance`
- `mart_target_vs_actual`
- `mart_attribution_summary`
- `mart_attribution_model_comparison`
- `mart_customer_value`
- `mart_budget_efficiency`
- `mart_data_quality_monitoring`

Primary metadata files:
- `openlineage_events.jsonl`
- `datahub_mces.json`
- `lineage_manifest.json`
