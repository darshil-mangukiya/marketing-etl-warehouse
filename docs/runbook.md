# Runbook and Troubleshooting

## Common Failures

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Airflow DAG quarantines batch | Rejected-row rate exceeded quality gate | Inspect `data/quality_reports/rejected_records/` and `latest_quality_summary.json`. |
| dbt source freshness failure | Source files were not loaded to PostgreSQL | Run `ingestion/load_postgres.py` and confirm raw tables exist. |
| Null spend failures | Source API returned incomplete paid media metrics | Check validation report rule `non_null_spend`; decide whether to quarantine or coalesce to zero in staging. |
| Attribution mismatch | Missing attribution IDs or inconsistent UTM campaign IDs | Review `attribution_id_present` warnings and campaign mapping coverage. |
| Orphan conversions | Sales conversion arrived before CRM lead or missing lead mapping | Check `known_lead_id_for_conversion` warnings and CDC arrival order. |
| Duplicate campaign-day rows | Platform exports contain duplicate campaign IDs or reprocessed records | Confirm processed-file hash state and campaign-day uniqueness logic. |

## Operational Checks

- Confirm `data/logs/ingestion_audit.jsonl` has recent successful source loads.
- Confirm `data/logs/watermarks.json` advanced after each incremental run.
- Confirm `data/quality_reports/latest_quality_summary.json` is generated after validation.
- Confirm `dbt build` succeeds before exporting BI tables.
- Confirm `data/exports/powerbi_export_manifest.json` lists all expected facts, dimensions, and marts.

## Recovery Steps

1. Re-run generation and ingestion for the same batch only if processed-file hashes were cleared intentionally.
2. For late-arriving data, keep the same source record ID and newer `updated_at`; incremental filters will pick it up.
3. If a source schema drifts, add the new field in staging and update tests.
4. If BI metrics diverge, reconcile from mart to fact to staging using the source-to-target mapping.
