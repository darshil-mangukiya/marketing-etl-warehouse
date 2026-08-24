# dbt Targets and Model Strategy

The single dbt project supports DuckDB (`duckdb`), PostgreSQL (`postgres`) and optional BigQuery (`bigquery`) targets. Models are not copied per adapter. Schema naming and reusable SQL differences belong in macros such as `generate_schema_name`, `surrogate_key`, `month_start`, `safe_divide` and `count_when`.

Local first-run order is raw generation/ingestion → `scripts/load_duckdb_raw.py` → `dbt build --project-dir dbt --profiles-dir dbt --target duckdb`. Running `dbt test` against an empty database produces missing-relation errors and is not the first-run command.

New models are `stg_ga4_events`, `int_ga4_sessions`, `mart_ga4_funnel`, `mart_marketing_variance_drivers` and `mart_campaign_action_center`. BigQuery profile/configuration and adapter-aware macros are implemented, but a live BigQuery build remains pending credentials and adapter installation. Existing SQL portability must be rechecked against a live target before claiming full BigQuery execution.
