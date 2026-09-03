# Setup Guide

## Local Smoke Run

```bash
cd marketing-etl-warehouse
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -B scripts/run_smoke_pipeline.py
python3 -B scripts/build_demo_marts.py
python3 -B scripts/generate_release_evidence.py
python3 -m pytest -q
```

This validates generation, ingestion, quality checks, watermarks, and monitoring without requiring PostgreSQL.

## Full Docker Run

```bash
cp .env.example .env
docker compose up -d --build postgres airflow-init airflow-api-server airflow-scheduler airflow-dag-processor
```

The `marketing` database credential, `admin` / `admin` Airflow login, and `local-dev-token` API token are local-only defaults. Override them in `.env` for any non-local use, and never commit a real `.env` file.

Open Airflow at `http://localhost:8080` with the configured Airflow credentials, then trigger `marketing_platform_daily`.

Optional application services:

```bash
docker compose up -d --build api-simulator dashboard
```

- FastAPI docs: `http://localhost:8000/docs`
- Streamlit dashboard: `http://localhost:8501`

## Manual Warehouse Run

```bash
python3 -B ingestion/pipeline.py --profile dev --generate
python3 -B ingestion/load_postgres.py
cd dbt
dbt build --profiles-dir .
cd ..
python3 -B scripts/export_bi_tables.py
```

Or run the full warehouse path:

```bash
python3 -B scripts/bootstrap_postgres.py
python3 -B scripts/run_warehouse_pipeline.py --profile smoke
```

The warehouse runner resets local watermark and processed-file state by default so the smoke run loads every source in the current batch, runs dbt with `--full-refresh`, exports facts/dimensions/marts, and records the result in `data/logs/warehouse_pipeline_latest.json`. Use `--preserve-ingestion-state` for incremental-behavior testing.

## API Simulator

The API simulator targets FastAPI `0.133.x` with Starlette `1.3.x`. These resolver-compatible bounds are kept in `requirements.txt`, the `api` optional dependency, and affected Dockerfiles so the API uses the security-remediated Starlette line consistently.

```bash
python3 -m pip install -r requirements.txt
uvicorn api_simulator.main:app --reload --port 8000
python3 -B ingestion/rest_api_client.py --base-url http://localhost:8000 --token local-dev-token
python3 -m pytest tests/test_api_simulator.py -q
```

Airflow is constrained to the secure 3.3.x line (`>=3.3.1,<3.4`) and the Docker runtime is pinned to `apache/airflow:3.3.1-python3.11`. The default `requirements.txt` supports local tests, release-site generation, dbt parsing, and the API simulator on modern local Python versions. Install `requirements-airflow.txt` only in a Python 3.11 environment when you need to run Airflow outside Docker. Airflow 3 runs the API server, scheduler, and DAG processor as separate services; the local Simple Auth Manager user is configured with `AIRFLOW_USER` and receives an administrator role.

## Data Quality and Reporting

```bash
python3 -B monitoring/great_expectations_runner.py --profile smoke
python3 -B local_ci/local_quality_gate.py
python3 -B scripts/generate_powerbi_semantic_model.py
python3 -B scripts/generate_lineage_metadata.py
python3 -B monitoring/observability_report.py
python3 -B scripts/generate_executive_report.py
```

## Large-Scale Dataset

Use `scale_test` only when you have sufficient disk and runtime available:

```bash
python3 -B ingestion/pipeline.py --profile scale_test --generate
```

The profile is configured for 5M+ Google Ads rows, 3M+ Facebook rows, 2M+ TikTok rows, 10M+ website analytics rows, 2M+ CRM rows, and 1M+ sales conversion rows.
