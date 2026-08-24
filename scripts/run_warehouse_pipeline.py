from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.load_postgres import load_raw_files
from ingestion.pipeline import run_pipeline
from scripts.bootstrap_postgres import bootstrap_postgres
from scripts.export_bi_tables import export_tables


def _timed_step(name: str, fn, *args, **kwargs) -> dict:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        result = fn(*args, **kwargs)
        status = "passed"
        error = None
    except Exception as exc:
        result = None
        status = "failed"
        error = str(exc)
    return {
        "step": name,
        "status": status,
        "started_at": started_at,
        "elapsed_seconds": time.perf_counter() - started,
        "result": result,
        "error": error,
    }


def _run_dbt_build(select: str | None = None, full_refresh: bool = True) -> dict:
    dbt_scratch = Path(tempfile.gettempdir()) / "marketing-etl-platform-dbt"
    dbt_log_path = dbt_scratch / "logs"
    dbt_target_path = dbt_scratch / "target"
    dbt_log_path.mkdir(parents=True, exist_ok=True)
    dbt_target_path.mkdir(parents=True, exist_ok=True)
    command = [
        "dbt",
        "--log-path",
        str(dbt_log_path),
        "build",
        "--target-path",
        str(dbt_target_path),
        "--profiles-dir",
        ".",
    ]
    if full_refresh:
        command.append("--full-refresh")
    if select:
        command.extend(["--select", select])
    completed = subprocess.run(command, cwd=PROJECT_ROOT / "dbt", text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "return_code": completed.returncode,
        "stdout_tail": completed.stdout[-5000:],
        "stderr_tail": completed.stderr[-5000:],
    }


def run_warehouse_pipeline(
    profile: str = "smoke",
    bootstrap: bool = True,
    generate: bool = True,
    truncate_raw: bool = True,
    export_limit: int | None = None,
    dbt_select: str | None = None,
    dbt_full_refresh: bool = True,
    reset_ingestion_state: bool = True,
) -> dict:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "steps": [],
    }
    if bootstrap:
        report["steps"].append(_timed_step("bootstrap_postgres", bootstrap_postgres))
    if reset_ingestion_state:
        report["steps"].append(_timed_step("reset_ingestion_state", _reset_ingestion_state))
    ingestion_step = _timed_step("generate_and_ingest", run_pipeline, profile, generate, True)
    report["steps"].append(ingestion_step)
    batch_id = (ingestion_step.get("result") or {}).get("batch_id")
    raw_files = _raw_files_for_batch(batch_id) if batch_id else None
    report["steps"].append(_timed_step("load_raw_postgres", load_raw_files, raw_files, truncate_raw))
    report["steps"].append(_timed_step("dbt_build", _run_dbt_build, dbt_select, dbt_full_refresh))
    if report["steps"][-1]["status"] == "passed" and report["steps"][-1]["result"]["return_code"] != 0:
        report["steps"][-1]["status"] = "failed"
        report["steps"][-1]["error"] = "dbt build returned a non-zero exit code"
    if all(step["status"] == "passed" for step in report["steps"]):
        report["steps"].append(_timed_step("export_bi_tables", export_tables, export_limit))
    report["status"] = "passed" if all(step["status"] == "passed" for step in report["steps"]) else "failed"
    output_path = PROJECT_ROOT / "data" / "logs" / "warehouse_pipeline_latest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def _raw_files_for_batch(batch_id: str) -> list[Path]:
    raw_root = PROJECT_ROOT / "data" / "lake" / "raw"
    return sorted(
        file_path
        for file_path in raw_root.rglob("*")
        if file_path.is_file() and f"batch_id={batch_id}" in file_path.parts
    )


def _reset_ingestion_state() -> dict:
    config = PlatformConfig.from_env()
    removed = []
    for path in (config.watermark_path, config.processed_files_path):
        if path.exists():
            path.unlink()
            removed.append(str(path.relative_to(PROJECT_ROOT)))
    return {"removed_files": removed}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full local PostgreSQL + dbt warehouse pipeline.")
    parser.add_argument("--profile", default="smoke")
    parser.add_argument("--no-bootstrap", action="store_true")
    parser.add_argument("--no-generate", action="store_true")
    parser.add_argument("--no-truncate-raw", action="store_true")
    parser.add_argument("--export-limit", type=int, default=None)
    parser.add_argument("--dbt-select", default=None)
    parser.add_argument("--no-dbt-full-refresh", action="store_true")
    parser.add_argument("--preserve-ingestion-state", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            run_warehouse_pipeline(
                profile=args.profile,
                bootstrap=not args.no_bootstrap,
                generate=not args.no_generate,
                truncate_raw=not args.no_truncate_raw,
                export_limit=args.export_limit,
                dbt_select=args.dbt_select,
                dbt_full_refresh=not args.no_dbt_full_refresh,
                reset_ingestion_state=not args.preserve_ingestion_state,
            ),
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
