# Modeled Stakeholder Requirements

These modeled requirements define how marketing leadership, channel managers, finance, revenue operations, BI, and data teams use the reporting platform.

| Stakeholder role | Reporting requirement | Decision supported | Acceptance criteria |
|---|---|---|---|
| Marketing leadership | Governed ROAS, CAC, revenue, spend, target attainment and exceptions | Allocate budget and request investigations | Totals reconcile to certified marts; stale/failed sources are visible |
| Channel manager | Campaign-level performance, target variance and deterministic action | Scale, monitor, reduce or fix campaigns | Every action shows the rule, reason, target and metric to monitor |
| Finance | Spend/revenue actuals against targets | Approve pacing and budget shifts | Monthly actuals reconcile to warehouse facts and governed targets |
| Revenue operations | GA4/session-to-lead-to-conversion journey | Repair funnel and attribution gaps | Lead/conversion identifiers and orphan conditions are validated |
| BI developer | Stable semantic model, DAX, relationships and refresh contract | Publish reliable reports | Keys, cardinality, refresh, RLS and visual checks are documented |
| Data engineering | Source health, retries, watermarks, rejection and load metadata | Operate ingestion | Source status includes counts, duration, retries, last watermark and failure class |
| Analytics engineering | Portable dbt sources, models, tests and KPI contracts | Change models safely | DuckDB remains green; BigQuery mode compiles/runs when credentials are supplied |

## Reporting and business rules

- Local datasets are generated and retain source labels through reporting.
- Live API/cloud status is `requires_credentials` until a credentialed run produces evidence.
- ROAS is revenue divided by spend; CAC is spend divided by closed-won conversions under the governed mart grain.
- Recommendations use deterministic, inspectable rules with human review.
- Diagnostic drivers identify contributing movements; causal analysis requires a separate method.
- A failed mapping or critical quality rule overrides performance recommendations with `DATA QUALITY HOLD`.
