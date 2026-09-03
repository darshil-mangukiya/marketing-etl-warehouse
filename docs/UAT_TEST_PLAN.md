# UAT, QA and Report Validation Plan

This plan separates automated verification from manual Power BI Desktop and Service acceptance. The 40 cases are in `docs/uat_test_cases.csv`; interface and stakeholder cases remain `NOT RUN` until execution and sign-off.

## Roles and entry criteria

- Data/analytics engineering prepares a green local quality gate, dbt build, source-contract report and reconciliation evidence.
- A modeled marketing product owner reviews business rules and acceptance criteria.
- A BI tester executes filter, relationship, DAX, refresh, RLS and visual cases after publishing/importing.
- Entry requires an identified data batch, documented build commit, no unresolved critical quality failure, and a stable semantic export.

## Test areas

- KPI and data reconciliation: ROAS, CAC, revenue, spend, attribution and targets.
- Business rule validation: variance severity, action thresholds and data-quality holds.
- GA4 funnel: event semantics, session rollup and purchase revenue.
- Report validation: slicers, date behavior, drill-through, missing values and source warnings.
- Cloud/refresh: optional BigQuery/GCS loads, credential failures, scheduled refresh and RLS.

## Exit criteria

- All critical cases pass with linked evidence.
- No open severity-1 reconciliation, privacy, credential or RLS defect.
- Any skipped credential/GUI case names its prerequisite and owner.
- Actual result, status and evidence fields are completed by the tester; they must not be pre-populated as passed.
