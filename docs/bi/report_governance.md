# Report Governance and Certification Lifecycle

The machine-readable registry is `governance/report_governance_registry.json` with a CSV review surface. Registry statuses drive the local report-governance workflow; Power BI Service certification is configured separately.

Lifecycle: `DRAFT → VALIDATED → APPROVED FOR REVIEW → DEPRECATED`.

Six assets are registered: the seven-page Power BI Desktop dashboard, Streamlit dashboard, live GA4 analytical output, scenario semantic asset, Marketing Action Center, and Data Quality / Source Health output. Each record includes modeled business/technical/data owners, sources, semantic model, refresh expectation, security classification, RLS state, validation, dependencies, limitations, certification state and evidence.
