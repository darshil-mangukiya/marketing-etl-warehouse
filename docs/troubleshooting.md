# Cloud Upgrade Troubleshooting

| Symptom | Likely cause | Safe resolution |
|---|---|---|
| Cloud mode names missing variables | `EXECUTION_MODE=cloud` without project/bucket | Set identifiers from `.env.example`; keep secrets outside Git |
| GCS/BigQuery/Secret Manager import error | Optional packages absent | Install `requirements-cloud.txt` in an isolated environment |
| Application Default Credentials error | No authorized identity | Run user-controlled ADC login or approved impersonation; do not download/share a key |
| Direct `dbt test` has missing schemas | Raw load/build not run | Load DuckDB raw and use `dbt build` for first run |
| BigQuery dataset mismatch | dbt dataset env vars differ from provisioned names | Align Terraform outputs and `BIGQUERY_*_DATASET` variables |
| Connector exhausts 429 retries | Vendor quota/rate limit | Reduce page/window size, honor Retry-After, wait, then retry |
| Connector error is intentionally vague | Response/token redaction | Inspect secure local request ID/status logs, never add tokens to logs |
| GA4 revenue validation fails | Revenue appears on non-purchase event | Correct source mapping or quarantine malformed event |
| Recommendation is held | Missing campaign mapping/quality failure | Repair mapping/quality issue before taking budget action |
| Power BI refresh fails | Credentials, privacy, region or gateway mismatch | Test BigQuery connection; use gateway only for retained local/on-prem sources |
