from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_HOME = Path(os.getenv("PROJECT_HOME", "/opt/airflow/project"))
if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

from ops.alerting import airflow_dag_success_alert, airflow_task_failure_alert


def task_failure_alert(context: dict) -> None:
    airflow_task_failure_alert(context)


def dag_success_alert(context: dict) -> None:
    airflow_dag_success_alert(context)
