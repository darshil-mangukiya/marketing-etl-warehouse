.PHONY: help setup smoke generate ingest validate ge-checkpoint contract-check catalog lineage-metadata semantic-package decision-intelligence final-validation benchmark scorecard dashboard evidence observability executive-report planning-report governance-pack pii-discovery retention-dry-run release-bundle release-site demo quality-gate test test-cov lint dbt-parse dbt-build dbt-test exports powerbi-exports powerbi-handoff analyst-outputs upgrade-outputs duckdb-raw demo-marts warehouse-run postgres-bootstrap security-views docker-up docker-down app

help:
	@echo "Targets: setup, smoke, duckdb-raw, dbt-parse, dbt-build, dbt-test, demo-marts, powerbi-handoff, analyst-outputs, evidence, demo, app, test"

setup:
	python3 -m pip install -r requirements.txt

smoke:
	python3 -B scripts/run_smoke_pipeline.py

generate:
	python3 -B data_sources/generate_sources.py --profile dev

ingest:
	python3 -B ingestion/pipeline.py --profile dev

validate:
	python3 -B monitoring/quality_checks.py --profile dev

ge-checkpoint:
	python3 -B monitoring/great_expectations_runner.py --profile dev

contract-check:
	python3 -B ingestion/data_contracts.py

catalog:
	python3 -B scripts/generate_catalog.py

lineage-metadata:
	python3 -B scripts/generate_lineage_metadata.py

semantic-package:
	python3 -B scripts/generate_powerbi_semantic_model.py

decision-intelligence:
	python3 -B scripts/generate_decision_intelligence.py

final-validation: decision-intelligence semantic-package powerbi-handoff
	python3 -B scripts/generate_final_validation_assets.py

benchmark:
	python3 -B benchmarks/pipeline_benchmark.py

scorecard:
	python3 -B ops/scorecard.py

dashboard:
	streamlit run bi_app/streamlit_app.py

app:
	streamlit run bi_app/streamlit_app.py

evidence: powerbi-handoff analyst-outputs
	python3 -B scripts/generate_release_evidence.py

observability:
	python3 -B monitoring/observability_report.py

executive-report:
	python3 -B scripts/generate_executive_report.py

planning-report:
	python3 -B scripts/generate_executive_planning_report.py

governance-pack:
	python3 -B scripts/generate_governance_pack.py

pii-discovery:
	python3 -B scripts/pii_discovery.py

retention-dry-run:
	python3 -B scripts/apply_retention_policy.py

release-bundle:
	python3 -B scripts/generate_release_bundle.py

release-site:
	python3 -B scripts/build_release_site.py

demo: smoke duckdb-raw dbt-parse dbt-build dbt-test demo-marts powerbi-exports decision-intelligence analyst-outputs semantic-package final-validation evidence observability executive-report planning-report governance-pack pii-discovery retention-dry-run release-bundle release-site
	@echo "Demo artifacts generated. Run: streamlit run bi_app/streamlit_app.py"

quality-gate:
	python3 -B local_ci/local_quality_gate.py

test:
	python3 -m pytest -q

test-cov:
	pytest --cov --cov-report=term-missing

lint:
	ruff check .
	python3 -m compileall -q .

dbt-parse:
	python3 -B scripts/run_logged_command.py reports/run_logs/dbt_parse.log -- dbt parse --project-dir dbt --profiles-dir dbt --target duckdb

dbt-build:
	python3 -B scripts/run_logged_command.py reports/run_logs/dbt_build.log -- dbt build --project-dir dbt --profiles-dir dbt --target duckdb

dbt-test:
	python3 -B scripts/run_logged_command.py reports/run_logs/dbt_test.log -- dbt test --project-dir dbt --profiles-dir dbt --target duckdb

exports:
	python3 -B scripts/export_bi_tables.py

duckdb-raw:
	python3 -B scripts/load_duckdb_raw.py

powerbi-exports: demo-marts analyst-outputs
	python3 -B scripts/generate_powerbi_handoff.py

powerbi-handoff: powerbi-exports

analyst-outputs: demo-marts
	python3 -B python_analysis/analyst_output_runner.py

upgrade-outputs: duckdb-raw dbt-build
	python3 -B scripts/export_cloud_upgrade_outputs.py

postgres-bootstrap:
	python3 -B scripts/bootstrap_postgres.py

security-views:
	psql -h localhost -d $${POSTGRES_DB:-marketing_warehouse} -f warehouse/postgres/views/security_views.sql

warehouse-run:
	python3 -B scripts/run_warehouse_pipeline.py --profile smoke

demo-marts:
	python3 -B scripts/build_demo_marts.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
