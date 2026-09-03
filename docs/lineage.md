# Cloud Upgrade Lineage

Original dbt/OpenLineage/DataHub/catalog artifacts remain under `metadata/generated`, `catalog/generated` and `docs/dbt_lineage.md`.

- GA4: generator or authorized export → `raw.ga4_events` → `stg_ga4_events` → `int_ga4_sessions` / `mart_ga4_funnel` → Power BI funnel visual.
- Paid media: vendor connector → local/GCS raw object → BigQuery raw → existing staging/unified campaign facts → campaign/channel marts.
- Diagnostics: `mart_channel_performance` → `mart_marketing_variance_drivers` → variance/root-driver visual and executive brief.
- Actions: campaign performance + target actuals + quality state → `mart_campaign_action_center` → action center visual/UAT.

Live GCS object URIs and BigQuery job IDs should be added to runtime lineage only after a credentialed run.
