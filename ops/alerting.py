from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def alert_path() -> Path:
    configured = Path(os.getenv("ALERT_LOG_PATH", PROJECT_ROOT / "data" / "logs" / "alerts.jsonl"))
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def emit_alert(
    severity: str,
    alert_type: str,
    message: str,
    context: dict | None = None,
) -> dict:
    payload = {
        "alert_id": f"alert_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
        "severity": severity,
        "alert_type": alert_type,
        "message": message,
        "context": context or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path = alert_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")
    return payload


def airflow_task_failure_alert(context: dict) -> dict:
    task_instance = context.get("task_instance")
    dag_run = context.get("dag_run")
    return emit_alert(
        severity="critical",
        alert_type="airflow_task_failure",
        message=f"Airflow task failed: {getattr(task_instance, 'task_id', 'unknown')}",
        context={
            "dag_id": getattr(task_instance, "dag_id", None),
            "task_id": getattr(task_instance, "task_id", None),
            "run_id": getattr(dag_run, "run_id", None),
            "execution_date": context.get("execution_date"),
            "exception": str(context.get("exception")),
        },
    )


def airflow_dag_success_alert(context: dict) -> dict:
    dag_run = context.get("dag_run")
    return emit_alert(
        severity="info",
        alert_type="airflow_dag_success",
        message="Marketing platform DAG completed successfully.",
        context={
            "dag_id": getattr(dag_run, "dag_id", None),
            "run_id": getattr(dag_run, "run_id", None),
            "state": getattr(dag_run, "state", None),
        },
    )
