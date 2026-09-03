from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
from airflow.sdk import DAG, TaskGroup, TriggerRule

PROJECT_HOME = Path(os.getenv("PROJECT_HOME", "/opt/airflow/project"))
if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))
DAG_DIR = Path(__file__).resolve().parent
if str(DAG_DIR) not in sys.path:
    sys.path.insert(0, str(DAG_DIR))

from common_callbacks import dag_success_alert, task_failure_alert


def generate_sources() -> None:
    from data_sources.generators import run_generation
    from ingestion.config import PlatformConfig

    run_generation(profile=os.getenv("DATA_PROFILE", "dev"), clean=True)
    if os.getenv("EXECUTION_MODE", "local") == "local" and os.getenv("DATA_PROFILE", "dev") == "smoke":
        config = PlatformConfig.from_env()
        for derived_state_path in (config.watermark_path, config.processed_files_path):
            derived_state_path.unlink(missing_ok=True)


def ingest_sources() -> dict:
    from ingestion.pipeline import run_pipeline

    return run_pipeline(profile=os.getenv("DATA_PROFILE", "dev"), generate=False)


def choose_api_extract_path() -> str:
    return "extract_mock_api_pages" if os.getenv("USE_MOCK_API_EXTRACTION", "false").lower() == "true" else "skip_mock_api_pages"


def extract_mock_api_pages() -> dict:
    from ingestion.rest_api_client import extract_mock_api_sources

    return extract_mock_api_sources(
        base_url=os.getenv("MOCK_API_BASE_URL", "http://api-simulator:8000"),
        token=os.getenv("MOCK_API_TOKEN", "local-dev-token"),
        page_size=int(os.getenv("MOCK_API_PAGE_SIZE", "1000")),
    )


def run_quality() -> dict:
    from monitoring.quality_checks import run_quality_checks

    return run_quality_checks(profile=os.getenv("DATA_PROFILE", "dev"))


def quality_gate() -> str:
    quality_path = PROJECT_HOME / "data" / "quality_reports" / "latest_quality_summary.json"
    if not quality_path.exists():
        return "quarantine_batch"
    summary = json.loads(quality_path.read_text(encoding="utf-8"))
    rejected_pct = summary["rejected_count"] / summary["row_count"] if summary["row_count"] else 0
    return "load_raw_to_postgres" if rejected_pct < 0.05 else "quarantine_batch"


def source_health() -> None:
    from monitoring.metrics import main

    main()


def record_source_extraction_mode(source_system: str) -> dict:
    """Record whether a source is synthetic or credential-dependent without claiming a live run."""
    mode = os.getenv("EXECUTION_MODE", "local").lower()
    credential_keys = {
        "google_ads": ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_REFRESH_TOKEN"],
        "meta_ads": ["META_ADS_ACCOUNT_ID", "META_ADS_ACCESS_TOKEN"],
        "tiktok_ads": ["TIKTOK_ADVERTISER_ID", "TIKTOK_ACCESS_TOKEN"],
        "ga4": ["GCP_PROJECT_ID", "BIGQUERY_RAW_DATASET"],
    }
    missing = [key for key in credential_keys[source_system] if not os.getenv(key)]
    status = "synthetic_local" if mode != "cloud" else "ready" if not missing else "requires_credentials"
    return {
        "source_system": source_system,
        "execution_mode": mode,
        "status": status,
        "missing_configuration": missing,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": task_failure_alert,
}


with DAG(
    dag_id="marketing_platform_daily",
    description="Daily multi-source marketing ingestion, validation, warehouse refresh, and BI export pipeline.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["marketing", "etl", "dbt", "warehouse", "bi", "gcp-ready"],
    on_success_callback=dag_success_alert,
) as dag:
    start = EmptyOperator(task_id="start")

    generate_source_data = PythonOperator(
        task_id="generate_source_data",
        python_callable=generate_sources,
    )

    with TaskGroup(group_id="extract_marketing_sources") as extract_marketing_sources:
        extract_google_ads = PythonOperator(
            task_id="extract_google_ads",
            python_callable=record_source_extraction_mode,
            op_kwargs={"source_system": "google_ads"},
        )
        extract_meta_ads = PythonOperator(
            task_id="extract_meta_ads",
            python_callable=record_source_extraction_mode,
            op_kwargs={"source_system": "meta_ads"},
        )
        extract_tiktok_ads = PythonOperator(
            task_id="extract_tiktok_ads",
            python_callable=record_source_extraction_mode,
            op_kwargs={"source_system": "tiktok_ads"},
        )
        extract_ga4 = PythonOperator(
            task_id="extract_ga4",
            python_callable=record_source_extraction_mode,
            op_kwargs={"source_system": "ga4"},
        )

    ingest_to_lake = PythonOperator(
        task_id="ingest_to_lake",
        python_callable=ingest_sources,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    choose_api_extract_path = BranchPythonOperator(
        task_id="choose_api_extract_path",
        python_callable=choose_api_extract_path,
    )

    extract_mock_api_pages = PythonOperator(
        task_id="extract_mock_api_pages",
        python_callable=extract_mock_api_pages,
    )

    skip_mock_api_pages = EmptyOperator(
        task_id="skip_mock_api_pages",
    )

    validate_lake = PythonOperator(
        task_id="validate_lake",
        python_callable=run_quality,
    )

    choose_load_path = BranchPythonOperator(
        task_id="choose_load_path",
        python_callable=quality_gate,
    )

    quarantine_batch = BashOperator(
        task_id="quarantine_batch",
        bash_command="echo 'Quality gate failed. Batch retained in raw zone with rejected-row outputs for investigation.'",
    )

    load_raw_to_postgres = BashOperator(
        task_id="load_raw_to_postgres",
        cwd=str(PROJECT_HOME),
        bash_command=(
            "python3 -B ingestion/load_postgres.py --truncate "
            "--batch-id \"{{ ti.xcom_pull(task_ids='ingest_to_lake')['batch_id'] }}\""
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        cwd=str(PROJECT_HOME / "dbt"),
        bash_command="dbt build --profiles-dir .",
    )

    export_powerbi_tables = BashOperator(
        task_id="export_powerbi_tables",
        cwd=str(PROJECT_HOME),
        bash_command="python3 -B scripts/export_bi_tables.py",
    )

    with TaskGroup(group_id="publish_bi_and_governance") as publish_bi_and_governance:
        build_demo_marts = BashOperator(
            task_id="build_demo_marts",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/build_demo_marts.py",
        )

        generate_decision_intelligence = BashOperator(
            task_id="generate_decision_intelligence",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_decision_intelligence.py",
        )

        generate_semantic_package = BashOperator(
            task_id="generate_semantic_package",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_powerbi_semantic_model.py",
        )

        generate_observability_report = BashOperator(
            task_id="generate_observability_report",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B monitoring/observability_report.py",
        )

        generate_executive_report = BashOperator(
            task_id="generate_executive_report",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_executive_report.py",
        )

        generate_planning_report = BashOperator(
            task_id="generate_planning_report",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_executive_planning_report.py",
        )

        generate_governance_release = BashOperator(
            task_id="generate_governance_release",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_governance_pack.py",
        )

        generate_pii_report = BashOperator(
            task_id="generate_pii_report",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/pii_discovery.py",
        )

        generate_retention_dry_run = BashOperator(
            task_id="generate_retention_dry_run",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/apply_retention_policy.py",
        )

        generate_release_bundle = BashOperator(
            task_id="generate_release_bundle",
            cwd=str(PROJECT_HOME),
            bash_command="python3 -B scripts/generate_release_bundle.py",
        )

        (
            build_demo_marts
            >> generate_decision_intelligence
            >> generate_semantic_package
            >> generate_observability_report
            >> generate_executive_report
            >> generate_planning_report
            >> generate_governance_release
            >> generate_pii_report
            >> generate_retention_dry_run
            >> generate_release_bundle
        )

    refresh_source_health = PythonOperator(
        task_id="refresh_source_health",
        python_callable=source_health,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    end = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    start >> generate_source_data >> extract_marketing_sources >> choose_api_extract_path
    choose_api_extract_path >> extract_mock_api_pages >> ingest_to_lake
    choose_api_extract_path >> skip_mock_api_pages >> ingest_to_lake
    ingest_to_lake >> validate_lake >> choose_load_path
    choose_load_path >> quarantine_batch >> refresh_source_health >> end
    choose_load_path >> load_raw_to_postgres >> dbt_build >> export_powerbi_tables >> publish_bi_and_governance >> refresh_source_health >> end
