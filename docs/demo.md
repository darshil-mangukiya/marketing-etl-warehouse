# Demo Runbook

This runbook walks through the local platform in operating order: source generation, ingestion, validation, warehouse modeling, BI assets, and reporting outputs.

## 1. Start With the System Context

The platform replaces spreadsheet stitching across paid media, web analytics, CRM, sales, targets, and reference mappings. The primary data questions are ROI, budget waste, funnel conversion, attribution disagreement, LTV, source freshness, and KPI certification.

Useful entry points:

- `README.md`
- `docs/architecture.md`
- `evidence/generated/architecture_snapshot.svg`
- `data_sources/config/source_volume.yml`

## 2. Generate and Ingest Source Data

Run a small end-to-end source flow:

```bash
python3 -B scripts/run_smoke_pipeline.py
```

Inspect:

- `data_sources/config/source_volume.yml`
- `ingestion/pipeline.py`
- `ingestion/watermarks.py`
- `data/lake/raw/`
- `data/logs/latest_ingestion_summary.json`
- `data/logs/watermarks.json`

## 3. Validate Raw Data and Source Contracts

Run validation:

```bash
python3 -B monitoring/great_expectations_runner.py --profile smoke
python3 -B ingestion/data_contracts.py
```

Review:

- `monitoring/quality_checks.py`
- `data/quality_reports/latest_quality_summary.csv`
- `data/quality_reports/rejected_records/`
- `monitoring/generated/observability_dashboard.html`

## 4. Review Warehouse and dbt Models

The warehouse separates raw ingestion, staging normalization, intermediate stitching, core facts/dimensions, and reporting marts.

Review:

- `dbt/models/staging/`
- `dbt/models/intermediate/`
- `dbt/models/marts/core/`
- `dbt/models/marts/reporting/`
- `dbt/models/marts/semantic_layer.yml`
- `docs/warehouse_model.md`

Optional local warehouse run:

```bash
python3 -B scripts/run_warehouse_pipeline.py --profile smoke
```

## 5. Build BI and Semantic Assets

Run:

```bash
python3 -B scripts/build_demo_marts.py
python3 -B scripts/generate_powerbi_semantic_model.py
streamlit run bi_app/streamlit_app.py
```

Review:

- `semantic_layer/kpi_catalog.md`
- `semantic_layer/dax_measure_catalog.md`
- `semantic_layer/powerbi_tmdl/`
- `semantic_layer/powerbi_pbip/`
- `data/exports/demo_mart_manifest.json`

Open the local dashboard at `http://localhost:8501`.

Recommended dashboard path:

- Executive
- Channels
- Optimization
- Attribution
- Planning
- Governance
- Action Center
- Quality

## 6. Generate Reporting Assets

Run:

```bash
python3 -B scripts/generate_release_evidence.py
python3 -B monitoring/observability_report.py
python3 -B scripts/generate_executive_report.py
python3 -B scripts/generate_governance_pack.py
python3 -B scripts/generate_release_bundle.py
```

Review:

- `reports/generated/governance_release_packet.html`
- `reports/generated/executive_marketing_report.html`
- `release/generated/release_index.html`
- `governance/generated/data_classification_catalog.csv`
- `governance/generated/access_policy_matrix.csv`
- `governance/generated/retention_policy_matrix.csv`

## 7. Run the Local Quality Gate

Run:

```bash
python3 -B local_ci/local_quality_gate.py
```

The result is written to `local_ci/latest_quality_gate.json` and checks ingestion, validation, contracts, marts, catalog generation, metadata, semantic packaging, reporting assets, governance outputs, pytest, and dbt parse.
