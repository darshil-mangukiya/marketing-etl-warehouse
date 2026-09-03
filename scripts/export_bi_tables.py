from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.database import get_engine

EXPORT_TABLES = [
    ("warehouse", "dim_date"),
    ("warehouse", "dim_campaign"),
    ("warehouse", "dim_channel"),
    ("warehouse", "dim_customer"),
    ("warehouse", "dim_region"),
    ("warehouse", "dim_device"),
    ("warehouse", "dim_product"),
    ("warehouse", "fact_campaign_performance"),
    ("warehouse", "fact_sessions"),
    ("warehouse", "fact_leads"),
    ("warehouse", "fact_conversions"),
    ("warehouse", "fact_revenue"),
    ("warehouse", "fact_targets"),
    ("warehouse", "fact_attribution"),
    ("mart", "mart_channel_performance"),
    ("mart", "mart_campaign_performance"),
    ("mart", "mart_funnel_performance"),
    ("mart", "mart_target_vs_actual"),
    ("mart", "mart_attribution_summary"),
    ("mart", "mart_attribution_model_comparison"),
    ("mart", "mart_customer_value"),
    ("mart", "mart_budget_efficiency"),
    ("mart", "mart_data_quality_monitoring"),
]


def export_tables(limit: int | None = None) -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    engine = get_engine()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_dir": str(config.export_dir.relative_to(config.project_root)),
        "tables": [],
    }
    with engine.begin() as connection:
        for schema, table in EXPORT_TABLES:
            query = f'select * from "{schema}"."{table}"'
            if limit:
                query += f" limit {int(limit)}"
            frame = pd.read_sql_query(text(query), connection)
            output_path = config.export_dir / f"{schema}_{table}.csv"
            frame.to_csv(output_path, index=False)
            manifest["tables"].append(
                {
                    "schema": schema,
                    "table": table,
                    "row_count": len(frame),
                    "file": str(output_path.relative_to(config.project_root)),
                }
            )
    manifest_path = config.export_dir / "powerbi_export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export BI-ready facts, dimensions, and marts to CSV.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit per table for sample exports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(export_tables(limit=args.limit), indent=2))


if __name__ == "__main__":
    main()
