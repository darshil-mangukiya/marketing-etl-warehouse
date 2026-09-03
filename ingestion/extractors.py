from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ingestion.config import PlatformConfig
from ingestion.file_io import read_frame
from ingestion.metadata import AuditLogger, IngestionAuditRecord, hash_file
from ingestion.s3_simulator import LocalS3DataLake
from ingestion.validators import (
    MarketingQualityValidator,
    write_rejected_records,
    write_validation_report,
)
from ingestion.watermarks import WatermarkStore


class IngestionManager:
    def __init__(self, config: PlatformConfig | None = None) -> None:
        self.config = config or PlatformConfig.from_env()
        self.config.ensure_dirs()
        self.audit = AuditLogger(self.config.log_dir)
        self.lake = LocalS3DataLake(self.config.data_lake_root)
        self.validator = MarketingQualityValidator()
        self.watermarks = WatermarkStore(self.config.watermark_path, self.config.processed_files_path)

    def ingest_manifest(self, manifest_path: Path | None = None) -> dict:
        manifest_path = manifest_path or self.config.source_manifest_path
        if not manifest_path.exists():
            raise FileNotFoundError(f"Source manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        batch_id = manifest["batch_id"]
        summary = {
            "batch_id": batch_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "sources": {},
            "status": "running",
        }
        starting_watermarks = {
            part["source_system"]: self.watermarks.get(part["source_system"])
            for part in manifest["parts"]
        }

        for part in manifest["parts"]:
            source_system = part["source_system"]
            source_path = self.config.project_root / part["path"]
            file_hash = hash_file(source_path)
            source_key = str(source_path.relative_to(self.config.project_root))
            if self.watermarks.is_processed(source_key, file_hash):
                self._record_source(summary, source_system, skipped=1)
                continue
            try:
                frame = read_frame(source_path)
                filtered_frame, load_type = self.watermarks.filter_incremental(
                    source_system,
                    frame,
                    watermark_override=starting_watermarks[source_system],
                )
                report, rejected = self.validator.validate_frame(source_system, filtered_frame)
                write_validation_report(report, self.config.quality_report_dir, batch_id, source_path.stem)
                rejected_path = self.lake.rejected_path(
                    self.config.quality_report_dir, source_system, batch_id, source_path
                )
                write_rejected_records(rejected, rejected_path)
                raw_path, actual_format = self.lake.write_raw(
                    filtered_frame, source_system, batch_id, source_path, part.get("file_format", "csv")
                )
                accepted_count = max(len(filtered_frame) - len(rejected), 0)
                self.watermarks.update_from_frame(source_system, filtered_frame)
                self.watermarks.mark_processed(source_key, file_hash, str(raw_path.relative_to(self.config.project_root)))
                self.audit.log_ingestion(
                    IngestionAuditRecord(
                        batch_id=batch_id,
                        source_system=source_system,
                        source_file=source_key,
                        raw_file=str(raw_path.relative_to(self.config.project_root)),
                        row_count=len(frame),
                        accepted_count=accepted_count,
                        rejected_count=len(rejected),
                        file_hash=file_hash,
                        load_type=load_type,
                        load_status="success",
                        failure_reason=None,
                        ingestion_time=datetime.now(timezone.utc).isoformat(),
                    )
                )
                self.audit.log_source_summary(
                    batch_id,
                    source_system,
                    {
                        "source_file": source_key,
                        "raw_file_format": actual_format,
                        "row_count": len(frame),
                        "accepted_count": accepted_count,
                        "quality_status": report.status,
                    },
                )
                self._record_source(
                    summary,
                    source_system,
                    files=1,
                    rows=len(frame),
                    accepted=accepted_count,
                    rejected=len(rejected),
                )
            except Exception as exc:
                self.audit.log_ingestion(
                    IngestionAuditRecord(
                        batch_id=batch_id,
                        source_system=source_system,
                        source_file=source_key,
                        raw_file=None,
                        row_count=0,
                        accepted_count=0,
                        rejected_count=0,
                        file_hash=file_hash,
                        load_type="unknown",
                        load_status="failed",
                        failure_reason=str(exc),
                        ingestion_time=datetime.now(timezone.utc).isoformat(),
                    )
                )
                self._record_source(summary, source_system, failed=1)

        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        summary["status"] = "completed"
        self.watermarks.save()
        summary_path = self.config.log_dir / "latest_ingestion_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def _record_source(self, summary: dict, source_system: str, **increments: int) -> None:
        current = summary["sources"].setdefault(
            source_system,
            {"files": 0, "rows": 0, "accepted": 0, "rejected": 0, "failed": 0, "skipped": 0},
        )
        for key, value in increments.items():
            current[key] = current.get(key, 0) + value
