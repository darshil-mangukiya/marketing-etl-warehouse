# Reporting Reliability Monitoring

`artifacts/monitoring/reporting_reliability.json` records the refresh expectations used by project monitoring.

| Source path | Expected refresh | Threshold | Current classification |
|---|---|---:|---|
| Google Ads project source | Daily | 36 hours | FRESH when the latest local ingestion has rows and no failed files |
| Meta project source | Daily | 36 hours | FRESH under the same local control |
| TikTok project source | Daily | 36 hours | FRESH under the same local control |
| Generated GA4 | Daily | 36 hours | FRESH under the same local control |
| CRM | Daily | 36 hours | FRESH under the same local control |
| Sales | Daily | 36 hours | FRESH under the same local control |
| Marketing targets | Monthly | 744 hours | FRESH when the monthly partition is present |
| Live GA4 Daily export | Daily | 48 hours | WARNING based on the last locally documented `events_20260819` table; no new BigQuery job was run solely for freshness |

Each structured row includes expected refresh, threshold, latest record/load metadata, volume expectation, missing-partition result, validation status, reliability status and execution classification. Allowed states are `FRESH`, `WARNING`, `BREACHED`, and `NOT APPLICABLE`.
