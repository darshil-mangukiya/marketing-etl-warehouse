from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.file_io import read_frame
from ingestion.validators import (
    MarketingQualityValidator,
    write_rejected_records,
    write_validation_report,
)


def discover_lake_files(config: PlatformConfig, zone: str = "raw") -> list[Path]:
    root = config.data_lake_root / zone
    files: list[Path] = []
    for pattern in ("*.csv", "*.jsonl", "*.parquet"):
        files.extend(root.rglob(pattern))
    return sorted(files)


def source_from_partition(path: Path) -> str:
    for part in path.parts:
        if part.startswith("source_system="):
            return part.split("=", 1)[1]
    raise ValueError(f"Could not infer source_system from {path}")


def run_quality_checks(profile: str = "dev", zone: str = "raw") -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    validator = MarketingQualityValidator()
    batch_id = f"quality_{profile}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    files = discover_lake_files(config, zone=zone)
    reports = []
    total_rows = 0
    total_rejections = 0

    for file_path in files:
        source_system = source_from_partition(file_path)
        frame = read_frame(file_path)
        report, rejected = validator.validate_frame(source_system, frame)
        total_rows += len(frame)
        total_rejections += len(rejected)
        report_path = write_validation_report(report, config.quality_report_dir, batch_id, file_path.stem)
        rejected_path = config.quality_report_dir / "rejected_records" / f"batch_id={batch_id}" / f"{file_path.stem}.csv"
        write_rejected_records(rejected, rejected_path)
        reports.append(
            {
                "source_system": source_system,
                "file": str(file_path.relative_to(config.project_root)),
                "report": str(report_path.relative_to(config.project_root)),
                "row_count": len(frame),
                "status": report.status,
                "issue_count": len(report.issues),
                "rejected_count": len(rejected),
            }
        )

    summary = {
        "batch_id": batch_id,
        "profile": profile,
        "zone": zone,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "row_count": total_rows,
        "rejected_count": total_rejections,
        "status": "passed" if all(report["status"] == "passed" for report in reports) else "failed",
        "reports": reports,
    }
    summary_path = config.quality_report_dir / "latest_quality_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.DataFrame(reports).to_csv(config.quality_report_dir / "latest_quality_summary.csv", index=False)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run custom data quality checks on lake files.")
    parser.add_argument("--profile", default="dev")
    parser.add_argument("--zone", default="raw", choices=["raw", "processed", "curated"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_quality_checks(profile=args.profile, zone=args.zone), indent=2))


if __name__ == "__main__":
    main()
