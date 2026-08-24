# BI Semantic Regression Validation

The local validator at `scripts/generate_final_validation_assets.py` checks the source-controlled BI contract. Power BI Desktop and Service checks run separately; machine-readable local results are stored in `artifacts/bi_validation/latest_bi_validation.json`.

## Validated contract

- 17 semantic tables and 59 unique DAX measures match the semantic manifest.
- Nine TMDL relationships match the source-controlled semantic-model manifest.
- Eleven import-handoff relationships match the broader Power BI relationship map and handoff manifest. The two counts describe different assets and are validated independently.
- Five conformed dimension exports have non-null, unique business keys, and all source-controlled TMDL table columns match their import CSV headers.
- Scenario output includes the required planning fields and is explicitly labeled `SIMULATED`.
- Executive, paid-channel and EMEA role definitions, predicates and target tables are present for later Power BI runtime testing.
- KPI definitions are complete, KPI-to-DAX references resolve, required Power BI-ready page specifications exist, manifest CSVs exist, and GA4 freshness/decision/reconciliation evidence is available.

## Failure behavior

Each check records an ID, affected asset, expected value, actual value, severity and PASS/FAIL status. Any failed error-level check makes the aggregate result fail and therefore fails the local quality gate.

## Scope boundary

This covers structural and data-contract regression testing. Visual rendering, Performance Analyzer, role impersonation, refresh, deployment, and certification are completed in Power BI Desktop or Service.
