# Changelog

All notable changes to this repository are documented here.

## v1.0.0 - 2026-05-17

Initial public release.

### Added

- Multi-source marketing data generator for paid media, web analytics, CRM, sales conversions, targets, and reference mappings.
- Python ingestion framework with API extraction, file ingestion, watermarks, audit metadata, rejected rows, and local S3-style lake zones.
- PostgreSQL warehouse schemas, dbt staging/intermediate/core/reporting models, semantic definitions, tests, and BI-ready marts.
- Airflow DAG for ingestion, validation, warehouse refresh, mart generation, exports, governance, and monitoring.
- Data quality framework with Great Expectations-style checks, source contracts, validation reports, and source health outputs.
- Streamlit BI command center, Power BI/TMDL-style semantic assets, DAX catalog, KPI documentation, and dashboard build notes.
- Governance artifacts for classification, access policies, retention, PII discovery, release certification, and operational scorecards.
- Local CI quality gate, GitHub Actions workflows, Docker Compose stack, Terraform scaffold, runbooks, and release bundle generation.
