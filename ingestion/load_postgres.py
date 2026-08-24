from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.database import execute_sql, get_engine
from ingestion.file_io import read_frame
from ingestion.sync_ops_metadata import sync_ops_metadata

CREATE_RAW_SCHEMA = """
create schema if not exists raw;
create schema if not exists ops;
create table if not exists ops.raw_load_history (
    raw_load_id bigserial primary key,
    source_system text not null,
    file_name text not null,
    row_count integer not null,
    loaded_at timestamptz not null default now()
);
create table if not exists ops.ingestion_logs (
    ingestion_log_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    file_name text not null,
    row_count integer not null,
    accepted_count integer not null,
    rejected_count integer not null,
    load_type text not null,
    load_status text not null,
    failure_reason text,
    ingestion_time timestamptz not null default now()
);
create table if not exists ops.source_audit (
    source_audit_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    source_file text,
    row_count integer,
    accepted_count integer,
    quality_status text,
    captured_at timestamptz not null default now()
);
create table if not exists ops.rejected_records (
    rejected_record_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    source_file text not null,
    rule_name text not null,
    payload jsonb not null,
    rejected_at timestamptz not null default now()
);
create table if not exists ops.watermarks (
    source_system text primary key,
    watermark_column text not null,
    watermark_value timestamptz not null,
    updated_at timestamptz not null default now()
);
create table if not exists ops.validation_results (
    validation_result_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    rule_name text not null,
    severity text not null,
    failed_count integer not null,
    status text not null,
    generated_at timestamptz not null default now()
);
"""


def discover_raw_files(config: PlatformConfig, batch_id: str | None = None) -> list[Path]:
    root = config.data_lake_root / "raw"
    files: list[Path] = []
    for suffix in ("*.csv", "*.jsonl", "*.parquet"):
        files.extend(root.rglob(suffix))
    if batch_id:
        batch_part = f"batch_id={batch_id}"
        files = [path for path in files if batch_part in path.parts]
    return sorted(files)


def source_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("source_system="):
            return part.split("=", 1)[1]
    raise ValueError(f"Could not infer source system from {path}")


def load_raw_files(files: list[Path] | None = None, truncate: bool = False, batch_id: str | None = None) -> dict:
    config = PlatformConfig.from_env()
    engine = get_engine()
    execute_sql(engine, CREATE_RAW_SCHEMA)
    files = files or discover_raw_files(config, batch_id=batch_id)
    summary = {"loaded_files": 0, "loaded_rows": 0, "tables": {}}
    truncated_tables: set[str] = set()
    with engine.begin() as connection:
        for file_path in files:
            source = source_from_path(file_path)
            table = source.lower().replace("-", "_")
            frame = read_frame(file_path)
            if frame.empty:
                continue
            if truncate and table not in truncated_tables:
                connection.exec_driver_sql(f'drop table if exists raw."{table}" cascade')
                truncated_tables.add(table)
            frame.to_sql(table, connection, schema="raw", if_exists="append", index=False, method="multi", chunksize=5000)
            pd.DataFrame(
                [{"source_system": source, "file_name": str(file_path), "row_count": len(frame)}]
            ).to_sql("raw_load_history", connection, schema="ops", if_exists="append", index=False)
            summary["loaded_files"] += 1
            summary["loaded_rows"] += len(frame)
            summary["tables"][table] = summary["tables"].get(table, 0) + len(frame)
    summary["ops_metadata"] = sync_ops_metadata(engine, config)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load raw lake files into PostgreSQL raw schema.")
    parser.add_argument("--truncate", action="store_true", help="Truncate raw tables before loading each file.")
    parser.add_argument("--batch-id", help="Load only lake files from this exact ingestion batch.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(load_raw_files(truncate=args.truncate, batch_id=args.batch_id))


if __name__ == "__main__":
    main()
