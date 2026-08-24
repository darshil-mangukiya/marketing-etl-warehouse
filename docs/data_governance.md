# GCP and Marketing Data Governance Addendum

Existing classification, access, retention, PII discovery, KPI certification, and governance outputs apply to the local platform. Extend them as follows when cloud mode is used:

- Treat GA4 user/session/attribution identifiers as pseudonymous and restricted; do not present them in executive marts.
- Limit raw vendor and GA4 datasets to pipeline/data roles; grant BI consumers read access to curated marts only.
- Use one keyless pipeline service account with dataset-scoped editor and bucket object access; no public bucket access.
- Store credentials in environment variables for local development or individual Secret Manager resources in cloud mode.
- Retain raw data only as long as the modeled use case requires; Terraform defaults raw tables to 90 days.
- Record execution mode, batch, source, watermark, hash and quality status without secret values.
- Maintain generated/live labeling across sources, models, and reports.
