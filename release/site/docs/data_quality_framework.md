# Data Quality Framework

The project uses layered validation to prevent unreliable source data from silently becoming trusted reporting data.

## Validation Layers

| Layer | Implementation | Purpose |
|---|---|---|
| Source contracts | `contracts/source_contracts.yml`, `ingestion/data_contracts.py` | Validate required columns, primary keys, data types, and source-level expectations |
| Ingestion validators | `ingestion/validators.py` | Check source-specific business rules and rejected records |
| Quality checks | `monitoring/quality_checks.py` | Produce quality summaries and rule-level failure outputs |
| Great Expectations | `great_expectations/` | Provide expectation suites and checkpoint configuration |
| dbt tests | `dbt/tests/`, model `schema.yml` files | Validate warehouse and mart-level relationships |
| Local quality gate | `local_ci/local_quality_gate.py` | Run pipeline, semantic, report, and test checks |

## Checks Covered

- duplicate campaigns and duplicate primary keys
- missing attribution IDs
- null or invalid spend records
- invalid dates
- impossible KPI relationships, such as clicks greater than impressions
- orphan conversions without matching leads
- missing campaign and region mappings
- schema drift
- source freshness failures
- rejected record volume
- data product scorecard and semantic KPI governance outputs

## Rejected Records

Rejected rows preserve operational context:

- source system
- source file
- rule name
- severity
- rejected row values
- failure reason
- batch ID
- ingestion timestamp

Rejected outputs are written under `data/quality_reports/` and summarized in monitoring outputs.

## Monitoring Outputs

| Output | Path |
|---|---|
| Quality summary | `data/quality_reports/latest_quality_summary.json` |
| Validation reports | `data/quality_reports/validation_reports/` |
| Rejected records | `data/quality_reports/rejected_records/` |
| Observability dashboard | `monitoring/generated/observability_dashboard.html` |
| Source health mart | `data/exports/demo_mart_source_health.csv` |
| Data quality mart | `data/exports/demo_mart_data_quality_monitoring.csv` |
| Local quality gate | `local_ci/latest_quality_gate.json` |

## Quality Gate Behavior

The smoke pipeline can contain intentionally invalid source rows. Validation separates them from accepted data and records the result. A batch is accepted when the configured quality gate passes and known rejected records are documented.
