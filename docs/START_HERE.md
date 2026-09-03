# Start Here

This page is the technical navigation index for the Campaign ROI Reporting Automation & Marketing Performance Analytics Platform.

## 1. Project Overview

- `README.md`
- `docs/business_case.md`
- `docs/project_scope_boundaries.md`

## 2. Architecture and Pipeline

- `docs/architecture.md`
- `docs/data_sources.md`
- `docs/pipeline_workflow.md`
- `docs/source_to_target_mapping.md`
- `airflow/dags/marketing_platform_daily.py`
- `ingestion/pipeline.py`

## 3. Warehouse and dbt

- `docs/warehouse_model.md`
- `docs/dbt_lineage.md`
- `dbt/models/staging/`
- `dbt/models/intermediate/`
- `dbt/models/marts/core/`
- `dbt/models/marts/reporting/`
- `dbt/tests/`

## 4. BI and Semantic Layer

- `bi_app/README.md`
- `bi_app/streamlit_app.py`
- `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`
- `dashboards/powerbi/README.md`
- `evidence/screenshots/powerbi/`
- `evidence/screenshots/streamlit/`
- `docs/dashboard_screenshot_checklist.md`
- `docs/dashboard_outputs.md`
- `semantic_layer/kpi_catalog.md`
- `semantic_layer/dax_measure_catalog.md`
- `semantic_layer/star_schema_relationship_map.md`
- `semantic_layer/dashboard_measure_matrix.md`
- `semantic_layer/powerbi/POWERBI_SETUP_GUIDE.md`
- `semantic_layer/powerbi_tmdl/`
- `semantic_layer/powerbi_pbip/`

## 5. Data Quality and Monitoring

- `docs/data_quality_framework.md`
- `monitoring/quality_checks.py`
- `monitoring/observability_report.py`
- `monitoring/generated/observability_dashboard.html`
- `local_ci/latest_quality_gate.json`

## 6. Business and BI Requirements

- `docs/business_requirements.md`
- `docs/stakeholder_map.md`
- `docs/user_stories_acceptance_criteria.md`
- `docs/uat_checklist.md`
- `docs/dashboard_requirements.md`
- `docs/business_insights_and_recommendations.md`
- `docs/business_decision_workflow.md`
- `semantic_layer/powerbi/POWERBI_EVIDENCE.md`
- `reports/generated/excel_ready/README.md`

## 7. Setup and Local Execution

- `docs/setup_guide.md`
- `docs/demo.md`
- `docs/runbook.md`
- `docs/execution_profiles.md`
- `docker-compose.yml`
- `Makefile`

Local BI dashboard:

```bash
python3 -B scripts/build_demo_marts.py
streamlit run bi_app/streamlit_app.py
```

## 8. Testing and Validation

- `tests/`
- `local_ci/local_quality_gate.py`
- `.github/workflows/local-quality-gate.yml`

## 9. Generated Outputs

- `evidence/generated/architecture_snapshot.svg`
- `evidence/generated/dashboard_wireframe.svg`
- `evidence/generated/dashboard_executive_preview.svg`
- `evidence/generated/dashboard_governance_preview.svg`
- `evidence/generated/dashboard_observability_preview.svg`
- `evidence/screenshots/streamlit/`
- `reports/generated/executive_marketing_report.html`
- `reports/generated/executive_planning_report.html`
- `reports/generated/governance_release_packet.html`
- `release/generated/release_manifest.json`
- `release/site/index.html`

## 10. Project Scope

- `docs/project_scope_boundaries.md`
- `docs/row_count_summary.md`
- `docs/incremental_load_evidence.md`
