# Incremental Loading

This document explains how the project handles watermarks, late-arriving records, duplicate reprocessing, and reruns.

## Where Incremental State Lives

| Artifact | Purpose |
|---|---|
| `ingestion/watermarks.py` | Watermark and processed-file store implementation |
| `data/logs/watermarks.json` | Last successful source watermark by source system |
| `data/logs/processed_files.json` | Source file hashes already processed |
| `data/logs/ingestion_audit.jsonl` | Batch/file-level audit records |
| `data/logs/latest_ingestion_summary.json` | Latest source-level ingestion summary |

## How Watermarks Work

`WatermarkStore` reads the latest watermark for each `source_system`. If a source frame has an `updated_at` column and a prior watermark exists, the ingestion layer keeps only records where `updated_at` is greater than the stored watermark. If no watermark exists, the load is treated as `full`.

Current watermark examples from `data/logs/watermarks.json`:

| Source System | Last Successful Watermark |
|---|---|
| `google_ads` | `2025-04-29T00:00:00` |
| `facebook_ads` | `2025-04-21T00:00:00` |
| `tiktok_ads` | `2025-04-26T00:00:00` |
| `website_analytics` | `2025-04-29T00:00:00` |
| `crm_leads` | `2025-04-28T00:00:00` |
| `sales_conversions` | `2025-07-12T00:00:00` |

## Duplicate Reprocessing Prevention

The pipeline hashes each source file and stores the result in `data/logs/processed_files.json`. On rerun, a file with the same path and hash can be skipped or treated as already processed. This prevents duplicate processing when the same batch is replayed.

## Late-Arriving Conversions

Sales conversions can have an `updated_at` value later than the lead or session date. The source watermark for `sales_conversions` allows the platform to ingest these later updates without reloading every historical record. Attribution and conversion marts can then be refreshed for affected periods.

## Example Audit Fields

Audit records are written to `data/logs/ingestion_audit.jsonl`.

| Field | Meaning |
|---|---|
| `source_system` | System that produced the source file |
| `batch_id` | Ingestion batch identifier |
| `load_type` | `full` or `incremental` |
| `row_count` | Source rows read |
| `accepted_count` | Rows accepted into the raw lake |
| `rejected_count` | Rows rejected by validation |
| `load_status` | Success/failure status |
| `failure_reason` | Failure detail if load failed |
| `file_hash` | Hash used for duplicate processing detection |

Example from the current batch:

| Source System | Batch ID | Load Type | Processed Row Count | Rejected Row Count | Rerun Behavior |
|---|---|---|---:|---:|---|
| `google_ads` | `batch_20260517T220817Z` | `full` | 1,004 | 8 | File hash is stored after success |
| `facebook_ads` | `batch_20260517T220817Z` | `full` | 1,004 | 7 | File hash is stored after success |
| `tiktok_ads` | `batch_20260517T220817Z` | `full` | 1,004 | 3 | File hash is stored after success |

## Rerun Behavior

| Scenario | Expected Behavior |
|---|---|
| New file, no watermark | Full load for that file/source |
| New file, existing watermark | Filter to records newer than the watermark |
| Same file and same hash | Avoid duplicate reprocessing |
| Same source with late conversion updates | Load records newer than the conversion watermark |
| Validation failure | Capture rejected rows and audit failure context |

## Local Verification Points

To verify incremental behavior during a local run, inspect:

- `data/logs/watermarks.json`
- `data/logs/processed_files.json`
- one sample `data/logs/ingestion_audit.jsonl` record
- Airflow task showing incremental/load step
