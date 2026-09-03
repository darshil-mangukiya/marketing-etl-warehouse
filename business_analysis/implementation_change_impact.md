# Implementation Change Impact

## Change objective

The current implementation consolidates data analysis, business analysis, and BI development assets into one traceable reporting platform. It strengthens planning, anomaly analysis, decision-intelligence automation, and BI handoff assets while preserving the existing ingestion, dbt, GA4, cloud, and reporting architecture.

## Reused capabilities

- Existing dbt variance-driver, funnel, attribution, target, quality, and campaign-action marts.
- Existing generated-data pipeline and live GA4 Daily BigQuery export path.
- Existing forecast, anomaly, scenario, action-center, Power BI, Streamlit, governance, and lineage assets.
- Existing 40-case acceptance-test corpus and reporting controls.

## Changes and impact

| Change | Affected assets | Expected impact | Risk/control |
|---|---|---|---|
| Consolidated BA package | `business_analysis/` | One auditable requirements/process/UAT/source package | Mappings are validated against tracked assets |
| Scenario engine | Analytics, tests, BI export | Reusable baseline/conservative/expected/aggressive/user-defined simulations | Explicit assumptions; zero-denominator and allocation checks |
| Anomaly diagnostics | Analytics and anomaly mart generation | Adds rolling, MAD, percentage, target, and requested KPI fields | Deterministic thresholds; no causal language |
| Reconciliation controls | Source, landing, warehouse, dbt, and BI checks | Makes count and metric differences explicit | Tolerances and unavailable checks are visible |
| Insight packet | Airflow and decision artifact | Provides one deterministic downstream contract | Works without external explanation services |
| BI semantic extension | Scenario table, DAX, page specs, RLS design | Strengthens planning/root-cause/action BI implementation | PBIX remains unchanged and accurately classified |

## Compatibility

- No live cloud resource change is required.
- Existing DuckDB and BigQuery model paths remain intact.
- The committed PBIX is not modified.
- Advertising-platform authorization status remains unchanged.
- New outputs are additive and deterministic.

## Deployment and adoption considerations

1. Run the local quality gate and artifact validators before using refreshed outputs.
2. Review scenario assumptions and anomaly thresholds with an authorized business owner before operational use.
3. Incorporate new Power BI-ready assets in Desktop, then complete GUI-specific UAT.
4. Configure identity mapping before treating RLS designs as deployable access control.
5. Retain explicit query limits and keyless cloud authentication.

## Rollback approach

The analytical and documentation extensions are additive. Rollback restores the prior source-controlled assets; it does not require a Terraform apply, database migration, or PBIX overwrite.
