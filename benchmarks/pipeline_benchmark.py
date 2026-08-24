from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def timed_command(command: list[str]) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True)
    elapsed_seconds = time.perf_counter() - started
    return {
        "command": " ".join(command),
        "return_code": completed.returncode,
        "elapsed_seconds": elapsed_seconds,
        "status": "passed" if completed.returncode == 0 else "failed",
        "stdout_tail": completed.stdout[-2500:],
        "stderr_tail": completed.stderr[-2500:],
    }


def run_pipeline_benchmark() -> dict:
    checks = [
        timed_command([sys.executable, "-B", "scripts/run_smoke_pipeline.py"]),
        timed_command([sys.executable, "-B", "monitoring/great_expectations_runner.py", "--profile", "smoke"]),
        timed_command([sys.executable, "-B", "ingestion/data_contracts.py"]),
        timed_command([sys.executable, "-B", "scripts/build_demo_marts.py"]),
        timed_command([sys.executable, "-B", "scripts/generate_catalog.py"]),
        timed_command([sys.executable, "-B", "scripts/generate_release_evidence.py"]),
        timed_command([sys.executable, "-B", "monitoring/observability_report.py"]),
        timed_command([sys.executable, "-B", "scripts/generate_executive_report.py"]),
    ]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if all(check["return_code"] == 0 for check in checks) else "failed",
        "total_elapsed_seconds": sum(check["elapsed_seconds"] for check in checks),
        "checks": checks,
    }
    output_dir = PROJECT_ROOT / "benchmarks" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pipeline_benchmark_latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    print(json.dumps(run_pipeline_benchmark(), indent=2))


if __name__ == "__main__":
    main()
