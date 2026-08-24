from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig


def load_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(records)


def build_source_health_summary() -> pd.DataFrame:
    config = PlatformConfig.from_env()
    audit = load_jsonl(config.log_dir / "ingestion_audit.jsonl")
    if audit.empty:
        return pd.DataFrame(
            columns=[
                "source_system",
                "last_ingestion_time",
                "successful_loads",
                "failed_loads",
                "total_rows",
                "rejected_rows",
                "health_status",
            ]
        )
    audit["ingestion_time"] = pd.to_datetime(audit["ingestion_time"], errors="coerce")
    grouped = audit.groupby("source_system", dropna=False).agg(
        last_ingestion_time=("ingestion_time", "max"),
        successful_loads=("load_status", lambda value: int((value == "success").sum())),
        failed_loads=("load_status", lambda value: int((value == "failed").sum())),
        total_rows=("row_count", "sum"),
        rejected_rows=("rejected_count", "sum"),
    )
    grouped["health_status"] = grouped.apply(
        lambda row: "degraded" if row["failed_loads"] else "healthy",
        axis=1,
    )
    return grouped.reset_index()


def main() -> None:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    health = build_source_health_summary()
    output = config.quality_report_dir / "source_health_summary.csv"
    health.to_csv(output, index=False)
    print(output)


if __name__ == "__main__":
    main()
