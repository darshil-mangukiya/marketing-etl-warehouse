# BigQuery Integration

`cloud_platform.bigquery.BigQueryWarehouse` initializes declared datasets idempotently and loads JSON rows only into configured layers. The dbt `bigquery` target maps raw, staging/intermediate, warehouse and mart schemas to environment-controlled datasets. DuckDB and PostgreSQL targets remain intact.

Required identifiers are `GCP_PROJECT_ID`, `GCP_REGION`, `BIGQUERY_RAW_DATASET`, `BIGQUERY_STAGING_DATASET`, `BIGQUERY_WAREHOUSE_DATASET` and `BIGQUERY_MART_DATASET`. Authentication uses Application Default Credentials (`BIGQUERY_AUTH_METHOD=oauth` for an interactive development machine). A service-account key is not created or committed.

Cost controls: on-demand queries only, colocated GCS/BigQuery regions, small project tables, partitioning or clustering only when table size justifies it, date-filtered development queries, no reservations, optional raw-table expiration, and a 100 MiB per-query dbt ceiling.

On 2026-08-18, Terraform provisioned `marketing_raw`, `marketing_staging`, `marketing_warehouse`, and `marketing_mart` in `us-central1`. A 70-row generated load populated seven raw tables; the selected dbt-bigquery lineage built 16 models and passed 24 tests (40/40 operations). On 2026-08-20, the isolated GA4 layer read `analytics_550433518.events_20260818` and `events_20260819`, built four relations, and passed 30 tests (34/34 operations). Detailed tables, row counts, and observed bytes are recorded in `P2_LIVE_GCP_VALIDATION.md`.
