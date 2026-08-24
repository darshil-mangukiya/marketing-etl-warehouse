# Stakeholder Map

| Stakeholder | Business Question | Decision Supported | Dashboard/Mart | KPI Focus | Data Quality Concern |
|---|---|---|---|---|---|
| CMO / VP Marketing | Which channels produce the strongest return? | Budget reallocation across channels | `mart_channel_performance`, Executive Overview | ROAS, CAC, revenue, gross margin, target attainment | Source freshness, attribution coverage |
| Growth Marketing Manager | Which campaigns should be scaled, fixed, or paused? | Campaign optimization and budget shift | `mart_campaign_performance`, `mart_campaign_optimization` | spend, conversions, attributed ROAS, waste flag | unmapped campaigns, missing attribution IDs |
| Sales Operations Manager | Which sources produce qualified leads and closed-won conversions? | Lead handoff and sales follow-up improvement | `mart_funnel_performance`, `mart_customer_value` | MQL rate, SQL rate, close rate, customer value | CRM stage completeness, orphan conversions |
| Finance Manager | Are spend and revenue tracking against plan? | Monthly pacing and target review | `mart_target_vs_actual`, `mart_budget_pacing` | spend attainment, revenue attainment, variance | target mapping completeness, month alignment |
| BI Developer | Are dashboard metrics governed and reproducible? | Semantic model and dashboard certification | `mart_semantic_kpi_governance`, Power BI assets | certified KPIs, relationship coverage, measure definitions | formula drift, relationship ambiguity |
| Data Engineer | Are source pipelines reliable and auditable? | Pipeline operations and incident review | `mart_source_health`, observability dashboard | freshness, rejected rows, failed files | schema drift, load failures, watermark gaps |
| Analytics Engineer | Are warehouse models reusable and traceable? | dbt model maintenance and mart ownership | dbt marts, lineage docs | mart grain, attribution weights, KPI validity | orphan facts, invalid keys, SCD windows |
| Executive Leadership | Can leadership trust the performance overview? | Executive operating review | Executive Overview, governance packet | revenue, margin, ROAS, target progress, action count | stale data, unresolved quality blockers |

