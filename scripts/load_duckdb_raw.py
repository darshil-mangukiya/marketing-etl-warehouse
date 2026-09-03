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


RAW_SOURCES = [
    "google_ads",
    "facebook_ads",
    "tiktok_ads",
    "website_analytics",
    "ga4_events",
    "crm_leads",
    "sales_conversions",
    "marketing_targets",
    "campaign_mapping",
    "region_mapping",
]


def _read_source(config: PlatformConfig, source_system: str) -> pd.DataFrame:
    root = config.data_lake_root / "raw" / f"source_system={source_system}"
    frames: list[pd.DataFrame] = []
    for pattern in ("*.csv", "*.jsonl", "*.parquet"):
        for path in sorted(root.rglob(pattern)):
            frame = read_frame(path)
            if "source_system" not in frame.columns:
                frame["source_system"] = source_system
            if "ingestion_available_at" not in frame.columns:
                frame["ingestion_available_at"] = datetime.now(timezone.utc).isoformat()
            frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def _ingestion_logs() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "logs" / "ingestion_audit.jsonl"
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "batch_id",
                "source_system",
                "row_count",
                "rejected_count",
                "load_status",
                "ingestion_time",
            ]
        )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    frame = pd.DataFrame(rows)
    if "accepted_count" in frame.columns and "row_count" not in frame.columns:
        frame["row_count"] = frame["accepted_count"]
    return frame


def _validation_results() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "quality_reports" / "latest_quality_summary.csv"
    if not path.exists():
        return pd.DataFrame(columns=["source_system", "rule_name", "severity", "failed_count", "generated_at"])
    quality = pd.read_csv(path)
    output = pd.DataFrame()
    output["source_system"] = quality.get("source_system", pd.Series(dtype=str))
    output["rule_name"] = "source_contract"
    output["severity"] = quality.get("status", "").map(lambda value: "error" if value == "failed" else "warning")
    output["failed_count"] = pd.to_numeric(quality.get("issue_count", 0), errors="coerce").fillna(0).astype(int)
    output["generated_at"] = datetime.now(timezone.utc).isoformat()
    return output


def load_duckdb_raw(database_path: Path) -> dict:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "duckdb is not installed. Install project dependencies with `python3 -m pip install -r requirements.txt`."
        ) from exc

    config = PlatformConfig.from_env()
    config.ensure_dirs()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": str(database_path.relative_to(PROJECT_ROOT)),
        "raw_tables": [],
    }
    try:
        connection.execute("create schema if not exists raw")
        connection.execute("create schema if not exists ops")
        for source_system in RAW_SOURCES:
            frame = _read_source(config, source_system)
            relation_name = f"raw.{source_system}"
            connection.execute(f"drop table if exists {relation_name}")
            if frame.empty:
                connection.execute(f"create table {relation_name} (source_system varchar, ingestion_available_at timestamp)")
                row_count = 0
            else:
                connection.register("source_frame", frame)
                connection.execute(f"create table {relation_name} as select * from source_frame")
                connection.unregister("source_frame")
                row_count = len(frame)
            manifest["raw_tables"].append({"table": relation_name, "row_count": row_count})

        for table_name, frame in {
            "ops.ingestion_logs": _ingestion_logs(),
            "ops.validation_results": _validation_results(),
        }.items():
            connection.execute(f"drop table if exists {table_name}")
            connection.register("ops_frame", frame)
            connection.execute(f"create table {table_name} as select * from ops_frame")
            connection.unregister("ops_frame")
            manifest["raw_tables"].append({"table": table_name, "row_count": len(frame)})
    finally:
        connection.close()

    output_path = PROJECT_ROOT / "data" / "logs" / "duckdb_raw_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load generated raw lake files into the local DuckDB demo warehouse.")
    parser.add_argument("--database", type=Path, default=PROJECT_ROOT / "data" / "warehouse" / "campaign_roi.duckdb")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(load_duckdb_raw(args.database), indent=2))


if __name__ == "__main__":
    main()
