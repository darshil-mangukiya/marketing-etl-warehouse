from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ingestion.file_io import append_jsonl


@dataclass(frozen=True)
class IngestionAuditRecord:
    batch_id: str
    source_system: str
    source_file: str
    raw_file: str | None
    row_count: int
    accepted_count: int
    rejected_count: int
    file_hash: str
    load_type: str
    load_status: str
    failure_reason: str | None
    ingestion_time: str


class AuditLogger:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.audit_path = log_dir / "ingestion_audit.jsonl"
        self.source_audit_path = log_dir / "source_audit.jsonl"

    def log_ingestion(self, record: IngestionAuditRecord) -> None:
        append_jsonl(self.audit_path, asdict(record))

    def log_source_summary(self, batch_id: str, source_system: str, metadata: dict) -> None:
        payload = {
            "batch_id": batch_id,
            "source_system": source_system,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            **metadata,
        }
        append_jsonl(self.source_audit_path, payload)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, default: dict | list | None = None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def dump_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
