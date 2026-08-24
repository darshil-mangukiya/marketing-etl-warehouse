# UAT Checklist

| Test Area | Test Case | Expected Result | Evidence File/Model | Status |
|---|---|---|---|---|
| KPI Validation | Validate ROAS calculation as booked revenue divided by spend. | ROAS matches KPI catalog and mart values. | `semantic_layer/kpi_catalog.md`, `demo_mart_channel_performance.csv` | Passed in demo evidence |
| KPI Validation | Validate CAC as spend divided by closed-won conversions. | CAC is blank/zero-safe when conversions are unavailable and matches mart totals. | `semantic_layer/dax_measure_catalog.md` | Ready for validation |
| Filter and Drilldown Validation | Filter channel performance by month, channel, and region. | Filtered totals reconcile to exported mart rows. | `mart_channel_performance`, Streamlit dashboard | Manual BI validation required |
| Filter and Drilldown Validation | Drill from channel to campaign. | Campaign detail is consistent with selected channel. | `mart_campaign_performance` | Manual BI validation required |
| Data Freshness Validation | Review source health before executive reporting. | Freshness/watermark status is visible by source. | `demo_mart_source_health.csv` | Passed in demo evidence |
| Source Reconciliation | Compare generated source row counts to ingestion summary. | Source counts, accepted rows, and rejected rows reconcile. | `docs/row_count_summary.md`, `local_ci/latest_quality_gate.json` | Passed in demo evidence |
| Dashboard Output Validation | Compare executive KPI cards to mart exports. | Spend, revenue, margin, ROAS, and quality alert totals match exports. | `demo_mart_executive_scorecard.csv` | Ready for validation |
| Attribution Logic Validation | Compare first-touch, last-touch, and weighted attribution totals. | Attribution model outputs are visible and assumptions are documented. | `fact_attribution.sql`, `mart_attribution_summary` | Ready for validation |
| Data Quality Validation | Review missing attribution, null spend, duplicate keys, and invalid KPI relationships. | Rejected rows and rule failures are visible with source context. | `data_quality_framework.md`, quality reports | Passed in demo evidence |
| Export Validation | Open Excel-ready CSV package and validate required sheets/files. | Required CSV files exist and contain data notes. | `reports/generated/excel_ready/` | Ready for validation |
| Performance / Usability Checks | Open local Streamlit dashboard using demo marts. | Dashboard loads locally and pages are navigable. | `bi_app/streamlit_app.py` | Manual BI validation required |
| Signoff Criteria | Confirm KPI, freshness, quality, and reconciliation checks before release. | No unresolved critical data-quality blocker for demo review. | `governance_release_packet.html` | Ready for validation |

## Signoff Criteria

- KPI totals reconcile to exported marts.
- Required filters and drilldowns work for the dashboard surface being reviewed.
- Data freshness/source health is checked before executive review.
- Data provenance is visible in documentation.
- Power BI screenshots and the committed `.pbix` should reconcile to the current exported marts before review.
- Rejected records and validation failures are documented before signoff.
