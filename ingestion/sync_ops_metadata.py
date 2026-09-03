from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

from ingestion.config import PlatformConfig
from ingestion.metadata import load_json


def _jsonl_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sync_ops_metadata(engine: Engine, config: PlatformConfig | None = None) -> dict:
    config = config or PlatformConfig.from_env()
    config.ensure_dirs()
    summary = {
        "ingestion_logs": 0,
        "source_audit": 0,
        "validation_results": 0,
        "watermarks": 0,
        "rejected_records": 0,
    }
    with engine.begin() as connection:
        ingestion_logs = _ingestion_log_frame(config)
        if not ingestion_logs.empty:
            _delete_batches(connection, "ops.ingestion_logs", ingestion_logs["batch_id"].dropna().unique().tolist())
            ingestion_logs.to_sql("ingestion_logs", connection, schema="ops", if_exists="append", index=False)
            summary["ingestion_logs"] = len(ingestion_logs)

        source_audit = _source_audit_frame(config)
        if not source_audit.empty:
            _delete_batches(connection, "ops.source_audit", source_audit["batch_id"].dropna().unique().tolist())
            source_audit.to_sql("source_audit", connection, schema="ops", if_exists="append", index=False)
            summary["source_audit"] = len(source_audit)

        validation_results = _validation_results_frame(config)
        if not validation_results.empty:
            _delete_batches(
                connection,
                "ops.validation_results",
                validation_results["batch_id"].dropna().unique().tolist(),
            )
            validation_results.to_sql("validation_results", connection, schema="ops", if_exists="append", index=False)
            summary["validation_results"] = len(validation_results)

        rejected_records = _rejected_records_frame(config)
        if not rejected_records.empty:
            _delete_batches(connection, "ops.rejected_records", rejected_records["batch_id"].dropna().unique().tolist())
            for record in rejected_records.to_dict(orient="records"):
                connection.execute(
                    text(
                        """
                        insert into ops.rejected_records
                            (batch_id, source_system, source_file, rule_name, payload)
                        values
                            (:batch_id, :source_system, :source_file, :rule_name, cast(:payload as jsonb))
                        """
                    ),
                    record,
                )
            summary["rejected_records"] = len(rejected_records)

        watermarks = load_json(config.watermark_path, default={})
        for source_system, payload in watermarks.items():
            if not payload.get("max_updated_at"):
                continue
            connection.execute(
                text(
                    """
                    insert into ops.watermarks (source_system, watermark_column, watermark_value, updated_at)
                    values (:source_system, 'updated_at', :watermark_value, now())
                    on conflict (source_system)
                    do update set
                        watermark_value = excluded.watermark_value,
                        updated_at = now()
                    """
                ),
                {"source_system": source_system, "watermark_value": payload["max_updated_at"]},
            )
            summary["watermarks"] += 1
    return summary


def _delete_batches(connection, table_name: str, batch_ids: list[str]) -> None:
    if not batch_ids:
        return
    statement = text(f"delete from {table_name} where batch_id in :batch_ids").bindparams(
        bindparam("batch_ids", expanding=True)
    )
    connection.execute(statement, {"batch_ids": batch_ids})


def _ingestion_log_frame(config: PlatformConfig) -> pd.DataFrame:
    records = _jsonl_records(config.log_dir / "ingestion_audit.jsonl")
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records)
    return pd.DataFrame(
        {
            "batch_id": frame["batch_id"],
            "source_system": frame["source_system"],
            "file_name": frame["source_file"],
            "row_count": frame["row_count"],
            "accepted_count": frame["accepted_count"],
            "rejected_count": frame["rejected_count"],
            "load_type": frame["load_type"],
            "load_status": frame["load_status"],
            "failure_reason": frame["failure_reason"],
            "ingestion_time": frame["ingestion_time"],
        }
    )


def _source_audit_frame(config: PlatformConfig) -> pd.DataFrame:
    records = _jsonl_records(config.log_dir / "source_audit.jsonl")
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records)
    return pd.DataFrame(
        {
            "batch_id": frame["batch_id"],
            "source_system": frame["source_system"],
            "source_file": frame.get("source_file"),
            "row_count": frame.get("row_count"),
            "accepted_count": frame.get("accepted_count"),
            "quality_status": frame.get("quality_status"),
            "captured_at": frame["captured_at"],
        }
    )


def _validation_results_frame(config: PlatformConfig) -> pd.DataFrame:
    records: list[dict] = []
    for report_path in (config.quality_report_dir / "validation_reports").rglob("*.json"):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        batch_id = "unknown"
        for part in report_path.parts:
            if part.startswith("batch_id="):
                batch_id = part.split("=", 1)[1]
                break
        for issue in report.get("issues", []):
            records.append(
                {
                    "batch_id": batch_id,
                    "source_system": issue["source_system"],
                    "rule_name": issue["rule_name"],
                    "severity": issue["severity"],
                    "failed_count": issue["failed_count"],
                    "status": report["status"],
                    "generated_at": report["generated_at"],
                }
            )
    return pd.DataFrame(records)


def _rejected_records_frame(config: PlatformConfig) -> pd.DataFrame:
    records: list[dict] = []
    for csv_path in (config.quality_report_dir / "rejected_records").rglob("*.csv"):
        source_system = "unknown"
        batch_id = "unknown"
        for part in csv_path.parts:
            if part.startswith("source_system="):
                source_system = part.split("=", 1)[1]
            if part.startswith("batch_id="):
                batch_id = part.split("=", 1)[1]
        frame = pd.read_csv(csv_path)
        for payload in frame.head(5000).to_dict(orient="records"):
            records.append(
                {
                    "batch_id": batch_id,
                    "source_system": source_system,
                    "source_file": csv_path.name,
                    "rule_name": "see_validation_report",
                    "payload": json.dumps(_json_safe(payload), default=str, allow_nan=False),
                }
            )
    return pd.DataFrame(records)


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
