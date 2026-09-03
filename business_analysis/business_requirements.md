# Marketing Performance, BI & Decision Intelligence Requirements

## Purpose and business problem

Marketing performance data arrives at different grains from paid media, web analytics, CRM, sales, targets, and reference mappings. Manual spreadsheet reconciliation makes KPI definitions, attribution, freshness, and recommended actions difficult to trust. The implementation translates modeled marketing requirements into governed source definitions, dimensional models, KPIs, DAX measures, acceptance criteria, and executive-ready reporting.

Generated campaign datasets make local execution reproducible without customer records. Events from the project website follow a separate GA4-to-BigQuery path. Advertising-platform connectors run through local contract and failure tests; vendor execution requires account authorization.

## Objectives

- Establish a traceable source-to-report path for spend, revenue, funnel, attribution, targets, quality, and actions.
- Make material performance changes explainable through deterministic variance and anomaly analysis.
- Support scenario comparison without presenting simulations as forecasts or approved decisions.
- Publish consistent Power BI, Streamlit, analyst, and decision-intelligence outputs.
- Keep recommendations transparent, quality-aware, and subject to human review.

## Modeled personas

| Persona | Modeled need | Decision supported |
|---|---|---|
| VP Marketing | Trusted performance, target gaps, and priority exceptions | Where to request deeper review or controlled reallocation |
| Marketing Analytics Manager | Reconciled KPI and driver analysis | Which movements and data issues warrant investigation |
| Performance Marketing Manager | Campaign/channel efficiency and actions | Scale, monitor, optimize, reduce, or hold for quality review |
| Finance Business Partner | Budget, revenue, CAC, and scenario transparency | Whether planning assumptions meet efficiency guardrails |
| Sales Operations Manager | Lead, qualification, conversion, and attribution flow | Where handoff or journey leakage requires follow-up |
| Data Analyst | Governed data and reusable analytical outputs | Trend, variance, anomaly, funnel, and scenario analysis |
| BI Developer | Stable semantic definitions and acceptance criteria | Build and validate usable reporting experiences |

These modeled consumer roles define reporting needs, decisions, and acceptance criteria for the documented business scenario.

## Business and functional requirements

| ID | Requirement | Persona | MoSCoW | Acceptance summary |
|---|---|---|---|---|
| BR-001 | Compare spend, revenue, ROAS, CAC, and margin by reporting period and channel. | VP Marketing | Must | Governed formulas reconcile to `mart_channel_performance`. |
| BR-002 | Identify campaign-level efficiency and waste conditions. | Performance Marketing Manager | Must | Campaign metrics reconcile at campaign/month grain. |
| BR-003 | Compare actual spend, revenue, leads, and conversions with targets. | Finance Business Partner | Must | Zero and missing targets are handled explicitly. |
| BR-004 | Explain period-over-period ROAS and CAC movement with deterministic drivers. | Marketing Analytics Manager | Must | Current, prior, absolute, and percentage variance reconcile. |
| BR-005 | Detect material KPI deviations with transparent thresholds and baselines. | Data Analyst | Must | Every anomaly records method, baseline, deviation, and severity. |
| BR-006 | Analyze CRM lead-stage leakage and sales conversion. | Sales Operations Manager | Must | Funnel counts and adjacent-stage rates reconcile. |
| BR-007 | Analyze generated GA4-style sessions and ecommerce stages locally. | Data Analyst | Should | Generated event/session totals reconcile and retain their provenance labels. |
| BR-008 | Analyze the project-site GA4 Daily export. | Marketing Analytics Manager | Must | Curated models include the approved hostname and exclude localhost. |
| BR-009 | Parse nested GA4 ecommerce items without inflating event counts. | Data Analyst | Must | Item grain is isolated and tested separately from event grain. |
| BR-010 | Compare attribution models and reconcile allocated revenue. | Marketing Analytics Manager | Must | Model weights and revenue reconcile within tolerance. |
| BR-011 | Surface stale, rejected, unmapped, or failed source conditions. | BI Developer | Must | Quality status is visible before reports are distributed. |
| BR-012 | Prevent quality failures from producing performance recommendations. | VP Marketing | Must | Critical quality conditions produce `DATA_QUALITY_HOLD`. |
| BR-013 | Prioritize transparent campaign actions with supporting metrics. | Performance Marketing Manager | Must | Action, reason, priority, and monitor metric are present. |
| BR-014 | Compare baseline, conservative, expected, aggressive, and user-defined budget scenarios. | Finance Business Partner | Should | All outputs are labeled simulations and derived from explicit assumptions. |
| BR-015 | Project clicks, sessions, conversions, customers, revenue, CAC, ROAS, and target variance. | Data Analyst | Should | Equations handle zero denominators and allocation totals safely. |
| BR-016 | Provide executive-ready performance and exception reporting. | VP Marketing | Must | KPI cards, trends, drivers, actions, and quality warnings are specified. |
| BR-017 | Support consistent date, channel, campaign, region, and device filtering where modeled. | BI Developer | Must | Filter scope and relationships are documented and acceptance-tested. |
| BR-018 | Provide drill-through from summary performance to campaign detail. | BI Developer | Should | Page specification defines drill-through keys and supporting detail. |
| BR-019 | Define reusable KPI formulas, grain, ownership, exclusions, and quality dependencies. | Marketing Analytics Manager | Must | KPI catalog maps to dbt and DAX assets. |
| BR-020 | Reconcile source, landing, warehouse, dbt, and BI-output counts and totals. | Data Analyst | Must | Reconciliation output identifies status and tolerance by check. |
| BR-021 | Automate deterministic validation, modeling, reconciliation, insights, and report generation. | BI Developer | Must | Airflow path works without optional external explanation services. |
| BR-022 | Preserve BigQuery query and infrastructure cost controls. | Finance Business Partner | Must | Selector/lookback and maximum-bytes safeguards remain documented and tested. |
| BR-023 | Provide acceptance tests with explicit execution states. | BI Developer | Must | Automated and GUI-dependent cases have distinct validation states. |
| BR-024 | Maintain role-specific navigation and implementation references. | Data Analyst | Could | Each documented capability links to source, test, or validation results. |

## Non-functional requirements

- **Reproducibility:** the DuckDB smoke path must run without cloud credentials.
- **Portability:** shared dbt models remain compatible with the supported local and BigQuery targets.
- **Security:** no keys, tokens, credential files, Terraform state, or secret values enter tracked artifacts.
- **Cost control:** live BigQuery selectors use explicit date windows and the configured per-query byte ceiling.
- **Traceability:** requirements map to sources, models, KPIs, DAX, report outputs, and tests.
- **Explainability:** anomalies, variance drivers, scenarios, and actions expose their methods and assumptions.
- **Usability:** reporting specifications cover navigation, consistent filters, titles, tooltips, contrast, and drill-through.
- **Truthfulness:** generated marketing data and project-site GA4 traffic remain visibly distinct.

## Business rules

1. ROAS equals governed revenue divided by marketing spend; CAC equals spend divided by closed-won conversions.
2. Undefined ratios remain null/blank rather than infinite or silently zeroed in reporting calculations.
3. Diagnostic contribution and anomaly signals identify associations, not causal impact.
4. Scenario outputs are simulations based on editable assumptions; they are not approved budgets or measured lift.
5. A critical data-quality issue overrides performance actions with `DATA_QUALITY_HOLD`.
6. Live GA4 curated models include only `p2.darshilmangukiya.com`; localhost data remains raw and excluded.
7. Advertising-platform connectors use local HTTP test transports; vendor extraction requires account authorization.
8. The committed PBIX contains seven pages, while additional page assets remain source-controlled specifications.

## User stories and acceptance criteria

- As a VP Marketing persona, I can see material target gaps and priority actions, so that I can request focused investigation. Acceptance: every action includes supporting metrics, a reason, priority, and human-review status.
- As a Marketing Analytics Manager persona, I can trace a KPI from source to report and UAT, so that metric disputes are resolvable. Acceptance: the traceability workbook references implemented models and measures.
- As a Performance Marketing Manager persona, I can compare campaign performance with transparent action rules. Acceptance: quality holds override optimization actions.
- As a Finance Business Partner persona, I can edit scenario assumptions and compare outcomes. Acceptance: allocations reconcile to 100% and outputs remain labeled simulation.
- As a Sales Operations Manager persona, I can inspect journey leakage and attribution gaps. Acceptance: funnel and attribution reconciliation tests pass.
- As a Data Analyst persona, I can reproduce trends, anomalies, and scenario outputs locally. Acceptance: unit tests and the DuckDB build pass.
- As a BI Developer persona, I can build report pages from governed tables, measures, relationships, RLS specifications, and acceptance tests. Acceptance: handoff validation passes and PBIX scope is stated accurately.

## Assumptions and dependencies

- Generated campaign, CRM, sales, target, and reference data represent a modeled business environment.
- Cloud validation uses Application Default Credentials; downloaded service-account keys are prohibited.
- Live vendor extraction requires separate credentials, consent, and authorization.
- Power BI Desktop is required to incorporate source-controlled page/semantic changes into the PBIX.
- Power BI Service deployment, scheduled refresh, and RLS enforcement use the Power BI interface.

## Operating boundaries

- Campaign, CRM, sales, and target metrics come from generated datasets; the GA4 path contains project-site events.
- Google Ads, Meta Ads, and TikTok Ads connectors currently use local HTTP test transports.
- Power BI assets run in Desktop; Service deployment, scheduled refresh, and runtime RLS validation are separate operating steps.
- UAT cases define acceptance procedures and record their current execution state.
- Scenario and forecast outputs support method review and planning discussion.
