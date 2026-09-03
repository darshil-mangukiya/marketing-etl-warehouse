from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.file_io import write_frame


class LocalS3DataLake:
    """Local filesystem implementation of a raw/processed/curated S3 layout."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def raw_partition_path(
        self,
        source_system: str,
        batch_id: str,
        source_file: Path,
        file_format: str,
    ) -> Path:
        load_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stem = source_file.stem.replace(".", "_")
        return (
            self.root
            / "raw"
            / f"source_system={source_system}"
            / f"load_date={load_date}"
            / f"batch_id={batch_id}"
            / f"{stem}.{file_format}"
        )

    def rejected_path(self, quality_report_dir: Path, source_system: str, batch_id: str, source_file: Path) -> Path:
        return (
            quality_report_dir
            / "rejected_records"
            / f"source_system={source_system}"
            / f"batch_id={batch_id}"
            / f"{source_file.stem}_rejected.csv"
        )

    def write_raw(
        self,
        frame: pd.DataFrame,
        source_system: str,
        batch_id: str,
        source_file: Path,
        file_format: str,
    ) -> tuple[Path, str]:
        return write_frame(frame, self.raw_partition_path(source_system, batch_id, source_file, file_format), file_format)
