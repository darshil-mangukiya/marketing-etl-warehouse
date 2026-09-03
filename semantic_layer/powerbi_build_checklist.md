# Power BI Build Checklist

1. Import exported CSVs from `data/exports/` or connect directly to PostgreSQL schemas.
2. Mark `dim_date[date_day]` as the date table.
3. Create one-direction relationships from dimensions to facts/marts.
4. Hide surrogate keys, ingestion metadata, row hashes, and CDC columns.
5. Add display folders: Executive KPIs, Efficiency, Engagement, Funnel, Attribution, Targets, Monitoring.
6. Validate measure totals against `mart_channel_performance` and `mart_target_vs_actual`.
7. Build executive pages from marts first; add drillthrough pages from facts second.
8. Add tooltips showing KPI definitions from `semantic_layer/kpi_catalog.md`.
9. Add a data quality page backed by `mart_data_quality_monitoring`.
10. Validate row counts against `data/exports/powerbi_export_manifest.json` or `data/exports/demo_mart_manifest.json`.
