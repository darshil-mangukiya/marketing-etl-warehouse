from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from google.cloud import bigquery

PROJECT_ID = "p2-marketing-analytics-505916"
LOCATION = "us-central1"
MAXIMUM_BYTES_BILLED = 104_857_600
EXPECTED_RELATIONS = {
    "marketing_raw": {
        "campaign_mapping": "TABLE",
        "facebook_ads": "TABLE",
        "google_ads": "TABLE",
        "region_mapping": "TABLE",
        "sales_conversions": "TABLE",
        "tiktok_ads": "TABLE",
        "website_analytics": "TABLE",
    },
    "marketing_staging": {
        "stg_campaign_mapping": "VIEW",
        "stg_facebook_ads": "VIEW",
        "stg_google_ads": "VIEW",
        "stg_region_mapping": "VIEW",
        "stg_sales_conversions": "VIEW",
        "stg_tiktok_ads": "VIEW",
        "stg_website_analytics": "VIEW",
        "int_campaign_spend_unified": "VIEW",
        "int_attribution_touchpoints": "VIEW",
        "int_campaign_daily": "VIEW",
    },
    "marketing_warehouse": {
        "dim_channel": "TABLE",
        "dim_source_system": "TABLE",
        "dim_region": "TABLE",
        "dim_campaign": "TABLE",
        "fact_campaign_performance": "TABLE",
    },
    "marketing_mart": {"mart_campaign_performance": "TABLE"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the BigQuery smoke relations and job usage.")
    parser.add_argument("--since-utc", default="2026-08-18T16:55:00+00:00")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    since = datetime.fromisoformat(args.since_utc)
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    relations: list[dict[str, object]] = []
    views: list[tuple[str, str]] = []
    for dataset, expected in EXPECTED_RELATIONS.items():
        for name, expected_type in expected.items():
            table = client.get_table(f"{PROJECT_ID}.{dataset}.{name}")
            actual_type = table.table_type
            if actual_type != expected_type:
                raise RuntimeError(f"{dataset}.{name} expected {expected_type}, found {actual_type}")
            relation = {
                "dataset": dataset,
                "name": name,
                "type": actual_type,
                "rows": int(table.num_rows) if table.num_rows is not None else None,
                "bytes": int(table.num_bytes) if table.num_bytes is not None else None,
            }
            relations.append(relation)
            if actual_type == "VIEW":
                views.append((dataset, name))

    count_expressions = [
        f"(select count(*) from `{PROJECT_ID}.{dataset}.{name}`) as `{name}`"
        for dataset, name in views
    ]
    count_sql = "select\n  " + ",\n  ".join(count_expressions)
    dry_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAXIMUM_BYTES_BILLED)
    dry_job = client.query(count_sql, job_config=dry_config, location=LOCATION)
    if int(dry_job.total_bytes_processed or 0) > MAXIMUM_BYTES_BILLED:
        raise RuntimeError("View-count verification exceeds the 100 MB safety ceiling")
    run_config = bigquery.QueryJobConfig(use_query_cache=False, maximum_bytes_billed=MAXIMUM_BYTES_BILLED)
    count_row = next(iter(client.query(count_sql, job_config=run_config, location=LOCATION).result()))
    view_counts = {name: int(count_row[name]) for _, name in views}
    for relation in relations:
        if relation["type"] == "VIEW":
            relation["rows"] = view_counts[str(relation["name"])]

    query_jobs = []
    load_jobs = []
    failed_jobs = 0
    for job in client.list_jobs(min_creation_time=since, all_users=False):
        if job.location and job.location.lower() != LOCATION:
            continue
        if job.error_result:
            failed_jobs += 1
        if isinstance(job, bigquery.QueryJob):
            query_jobs.append(job)
        elif isinstance(job, bigquery.LoadJob):
            load_jobs.append(job)

    report = {
        "verified_at": datetime.now().astimezone().isoformat(),
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "synthetic_only": True,
        "maximum_bytes_billed_per_query": MAXIMUM_BYTES_BILLED,
        "relation_count": len(relations),
        "relations": relations,
        "view_count_query_dry_run_bytes_processed": int(dry_job.total_bytes_processed or 0),
        "jobs_since_utc": since.isoformat(),
        "query_job_count": len(query_jobs),
        "load_job_count": len(load_jobs),
        "failed_job_count": failed_jobs,
        "query_bytes_processed": sum(int(job.total_bytes_processed or 0) for job in query_jobs),
        "query_bytes_billed": sum(int(job.total_bytes_billed or 0) for job in query_jobs),
    }
    repo_root = Path(__file__).resolve().parents[1]
    report_path = repo_root / "reports" / "generated" / "live_bigquery_smoke_verification.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
