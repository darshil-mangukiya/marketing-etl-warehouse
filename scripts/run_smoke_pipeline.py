from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.generators import run_generation
from ingestion.pipeline import run_pipeline
from monitoring.metrics import build_source_health_summary
from monitoring.quality_checks import run_quality_checks


def clean_runtime_outputs() -> None:
    runtime_dirs = [
        PROJECT_ROOT / "data_sources" / "generated",
        PROJECT_ROOT / "data" / "lake" / "raw",
        PROJECT_ROOT / "data" / "lake" / "processed",
        PROJECT_ROOT / "data" / "lake" / "curated",
        PROJECT_ROOT / "data" / "quality_reports",
        PROJECT_ROOT / "data" / "exports",
        PROJECT_ROOT / "data" / "logs",
    ]
    for directory in runtime_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        for child in directory.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def main() -> None:
    clean_runtime_outputs()
    manifest = run_generation(profile="smoke", clean=True)
    ingestion_summary = run_pipeline(profile="smoke", generate=False)
    quality_summary = run_quality_checks(profile="smoke")
    source_health = build_source_health_summary()
    rejected_rate = (
        quality_summary["rejected_count"] / quality_summary["row_count"]
        if quality_summary["row_count"]
        else 0
    )
    output = {
        "manifest": manifest.to_dict(),
        "ingestion_summary": ingestion_summary,
        "quality_summary": {
            "batch_id": quality_summary["batch_id"],
            "file_count": quality_summary["file_count"],
            "row_count": quality_summary["row_count"],
            "rejected_count": quality_summary["rejected_count"],
            "status": quality_summary["status"],
            "quality_gate": "pass" if rejected_rate < 0.05 else "quarantine",
        },
        "source_health_rows": len(source_health),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
