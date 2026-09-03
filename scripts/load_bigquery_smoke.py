from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

PROJECT_ID = "p2-marketing-analytics-505916"
LOCATION = "us-central1"
DATASET_ID = "marketing_raw"
MAX_ROWS_PER_SOURCE = 10
SOURCE_FORMATS = {
    "campaign_mapping": "csv",
    "facebook_ads": "csv",
    "google_ads": "jsonl",
    "region_mapping": "csv",
    "sales_conversions": "jsonl",
    "tiktok_ads": "parquet",
    "website_analytics": "parquet",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a small generated BigQuery smoke subset.")
    parser.add_argument("--dry-run", action="store_true", help="Read and validate local sources without writing to BigQuery.")
    parser.add_argument("--rows-per-source", type=int, default=MAX_ROWS_PER_SOURCE)
    return parser.parse_args()


def read_source(repo_root: Path, source: str, source_format: str, row_limit: int) -> tuple[pd.DataFrame, list[str]]:
    source_root = repo_root / "data_sources" / "generated" / f"source_system={source}"
    patterns = {"csv": "*.csv", "jsonl": "*.jsonl", "parquet": "*.parquet"}
    files = sorted(source_root.glob(f"batch_id=*/{patterns[source_format]}"))
    if not files:
        raise FileNotFoundError(f"No generated {source_format} files found for {source} under {source_root}")

    frames: list[pd.DataFrame] = []
    used_files: list[str] = []
    remaining = row_limit
    for path in files:
        if remaining <= 0:
            break
        if source_format == "csv":
            frame = pd.read_csv(path, nrows=remaining)
        elif source_format == "jsonl":
            frame = pd.read_json(path, lines=True).head(remaining)
        else:
            frame = pd.read_parquet(path).head(remaining)
        if not frame.empty:
            frames.append(frame)
            used_files.append(str(path.relative_to(repo_root)))
            remaining -= len(frame)

    if not frames:
        raise ValueError(f"Generated source {source} contained no rows")
    result = pd.concat(frames, ignore_index=True).head(row_limit)
    if result.columns.duplicated().any():
        raise ValueError(f"Generated source {source} has duplicate columns")
    return result, used_files


def assert_safe_destination(client: bigquery.Client, table_id: str) -> None:
    try:
        table = client.get_table(table_id)
    except NotFound:
        return
    labels = table.labels or {}
    if labels.get("validation") != "bounded_smoke" or labels.get("data_class") != "synthetic":
        raise RuntimeError(f"Refusing to overwrite existing non-smoke table {table_id}")


def main() -> int:
    args = parse_args()
    if args.rows_per_source < 1 or args.rows_per_source > MAX_ROWS_PER_SOURCE:
        raise ValueError(f"--rows-per-source must be between 1 and {MAX_ROWS_PER_SOURCE}")

    repo_root = Path(__file__).resolve().parents[1]
    prepared: dict[str, tuple[pd.DataFrame, list[str]]] = {
        source: read_source(repo_root, source, source_format, args.rows_per_source)
        for source, source_format in SOURCE_FORMATS.items()
    }

    report: dict[str, object] = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "dataset_id": DATASET_ID,
        "synthetic_only": True,
        "dry_run": args.dry_run,
        "rows_per_source_limit": args.rows_per_source,
        "tables": [],
    }

    client = None if args.dry_run else bigquery.Client(project=PROJECT_ID, location=LOCATION)
    for source, (frame, used_files) in prepared.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{source}"
        entry: dict[str, object] = {
            "table_id": table_id,
            "rows": len(frame),
            "columns": list(frame.columns),
            "source_files": used_files,
        }
        if client is not None:
            assert_safe_destination(client, table_id)
            job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
            job = client.load_table_from_dataframe(frame, table_id, job_config=job_config, location=LOCATION)
            job.result()
            table = client.get_table(table_id)
            table.labels = {**(table.labels or {}), "data_class": "synthetic", "validation": "bounded_smoke"}
            client.update_table(table, ["labels"])
            load_stats = job._properties.get("statistics", {}).get("load", {})
            entry.update(
                {
                    "loaded_rows": int(job.output_rows or 0),
                    "table_rows": int(table.num_rows),
                    "table_bytes": int(table.num_bytes),
                    "load_input_bytes": int(load_stats.get("inputFileBytes", 0)),
                }
            )
        report["tables"].append(entry)

    report["total_rows"] = sum(int(table["rows"]) for table in report["tables"])
    report_path = repo_root / "reports" / "generated" / "live_bigquery_smoke_raw_load.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
