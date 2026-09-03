from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else PROJECT_ROOT / value


@dataclass(frozen=True)
class PlatformConfig:
    project_root: Path
    data_lake_root: Path
    quality_report_dir: Path
    export_dir: Path
    log_dir: Path
    source_manifest_path: Path
    watermark_path: Path
    processed_files_path: Path

    @classmethod
    def from_env(cls) -> PlatformConfig:
        data_lake_root = _path_from_env("DATA_LAKE_ROOT", "data/lake")
        quality_report_dir = _path_from_env("QUALITY_REPORT_DIR", "data/quality_reports")
        export_dir = _path_from_env("EXPORT_DIR", "data/exports")
        log_dir = _path_from_env("LOG_DIR", "data/logs")
        source_manifest_path = PROJECT_ROOT / "data_sources" / "generated" / "manifest.json"
        return cls(
            project_root=PROJECT_ROOT,
            data_lake_root=data_lake_root,
            quality_report_dir=quality_report_dir,
            export_dir=export_dir,
            log_dir=log_dir,
            source_manifest_path=source_manifest_path,
            watermark_path=log_dir / "watermarks.json",
            processed_files_path=log_dir / "processed_files.json",
        )

    def ensure_dirs(self) -> None:
        for path in [
            self.data_lake_root / "raw",
            self.data_lake_root / "processed",
            self.data_lake_root / "curated",
            self.quality_report_dir,
            self.export_dir,
            self.log_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def postgres_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "marketing_warehouse")
    user = os.getenv("POSTGRES_USER", "marketing")
    password = os.getenv("POSTGRES_PASSWORD", "marketing")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
