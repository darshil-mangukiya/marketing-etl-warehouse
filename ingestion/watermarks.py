from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.metadata import dump_json, load_json

_WATERMARK_SENTINEL = object()


class WatermarkStore:
    def __init__(self, watermark_path: Path, processed_files_path: Path) -> None:
        self.watermark_path = watermark_path
        self.processed_files_path = processed_files_path
        self._watermarks: dict = load_json(watermark_path, default={})
        self._processed: dict = load_json(processed_files_path, default={})

    def get(self, source_system: str) -> pd.Timestamp | None:
        value = self._watermarks.get(source_system, {}).get("max_updated_at")
        return pd.Timestamp(value) if value else None

    def update_from_frame(self, source_system: str, frame: pd.DataFrame) -> None:
        if "updated_at" not in frame.columns or frame.empty:
            return
        max_updated_at = pd.to_datetime(frame["updated_at"], errors="coerce").max()
        if pd.isna(max_updated_at):
            return
        current = self.get(source_system)
        if current is None or max_updated_at > current:
            self._watermarks[source_system] = {
                "max_updated_at": max_updated_at.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

    def is_processed(self, source_file: str, file_hash: str) -> bool:
        return self._processed.get(source_file, {}).get("file_hash") == file_hash

    def mark_processed(self, source_file: str, file_hash: str, raw_file: str) -> None:
        self._processed[source_file] = {
            "file_hash": file_hash,
            "raw_file": raw_file,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    def filter_incremental(
        self,
        source_system: str,
        frame: pd.DataFrame,
        watermark_override: pd.Timestamp | object = _WATERMARK_SENTINEL,
    ) -> tuple[pd.DataFrame, str]:
        watermark = self.get(source_system) if watermark_override is _WATERMARK_SENTINEL else watermark_override
        if watermark is None or "updated_at" not in frame.columns:
            return frame, "full"
        updated_at = pd.to_datetime(frame["updated_at"], errors="coerce")
        return frame.loc[updated_at > watermark].copy(), "incremental"

    def save(self) -> None:
        dump_json(self.watermark_path, self._watermarks)
        dump_json(self.processed_files_path, self._processed)
