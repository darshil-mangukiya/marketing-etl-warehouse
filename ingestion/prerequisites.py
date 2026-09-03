from __future__ import annotations

import json
import tempfile
from pathlib import Path

from data_sources.generators import (
    DEFAULT_CONFIG,
    SyntheticMarketingGenerator,
    load_profile,
)
from ingestion.config import PROJECT_ROOT, PlatformConfig
from ingestion.extractors import IngestionManager

INGESTION_SUMMARY_RELATIVE_PATH = Path("data/logs/latest_ingestion_summary.json")


def _validate_ingestion_summary(summary: object) -> dict:
    if not isinstance(summary, dict):
        raise ValueError("ingestion summary must be a JSON object")
    if summary.get("status") != "completed":
        raise ValueError("ingestion summary status is not completed")
    sources = summary.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ValueError("ingestion summary does not contain source results")
    failed_sources = [
        name
        for name, result in sources.items()
        if not isinstance(result, dict) or int(result.get("failed", 0)) > 0
    ]
    if failed_sources:
        raise ValueError(f"ingestion summary contains failed sources: {', '.join(failed_sources)}")
    return summary


def _build_ingestion_summary(project_root: Path, temporary_root: Path) -> dict:
    profile = load_profile(DEFAULT_CONFIG, "smoke")
    source_root = temporary_root / "generated_sources"
    generator = SyntheticMarketingGenerator(
        start_date=profile["start_date"],
        end_date=profile["end_date"],
        output_root=source_root,
    )
    generator.generate_all(
        profile="smoke",
        row_counts=profile["row_counts"],
        formats=profile["formats"],
        chunk_size=int(profile["chunk_size"]),
        clean=True,
    )

    runtime_root = temporary_root / "runtime"
    log_dir = runtime_root / "logs"
    config = PlatformConfig(
        project_root=temporary_root,
        data_lake_root=runtime_root / "lake",
        quality_report_dir=runtime_root / "quality_reports",
        export_dir=runtime_root / "exports",
        log_dir=log_dir,
        source_manifest_path=source_root / "manifest.json",
        watermark_path=log_dir / "watermarks.json",
        processed_files_path=log_dir / "processed_files.json",
    )
    return IngestionManager(config=config).ingest_manifest(config.source_manifest_path)


def ensure_ingestion_summary(
    project_root: Path = PROJECT_ROOT,
    output_path: Path | None = None,
) -> dict:
    target = output_path or project_root / INGESTION_SUMMARY_RELATIVE_PATH
    if target.exists():
        try:
            return _validate_ingestion_summary(json.loads(target.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass

    try:
        with tempfile.TemporaryDirectory(prefix="p2-ingestion-prerequisite-") as directory:
            summary = _validate_ingestion_summary(
                _build_ingestion_summary(project_root, Path(directory))
            )
    except Exception as exc:
        raise RuntimeError(
            "Required generated ingestion summary "
            "`data/logs/latest_ingestion_summary.json` is unavailable and safe local "
            "generation failed. Decision-intelligence and BI validation are blocked. "
            "Run `python3 -B scripts/run_smoke_pipeline.py` and retry."
        ) from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_target = target.with_suffix(f"{target.suffix}.tmp")
    try:
        temporary_target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        temporary_target.replace(target)
    finally:
        temporary_target.unlink(missing_ok=True)
    return summary
