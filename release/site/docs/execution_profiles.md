# Execution Profiles

The project supports small, repeatable local execution and a documented high-volume generation profile. The scale configuration remains explicit while the default path runs comfortably on a laptop.

| Profile | Purpose | Approx Row Volume | Runtime Notes | Best Used For |
|---|---|---:|---|---|
| Smoke Mode (`smoke`) | Fast local run with source generation, ingestion, validation, DuckDB raw load, marts, and reports | 11,052 generated source rows in the current manifest | Runs quickly on a laptop and is suitable for repeatable validation; use `make demo` after installing dependencies | local testing, CI checks, report generation, dashboard review, Power BI handoff CSVs |
| Development Profile (`dev`) | Larger local run for model and report testing | about 237,720 configured source rows | Heavier than smoke mode but still intended for local development | transformation testing, report stress checks, local QA |
| Scale Profile (`scale_test`) | Large-volume generation profile | about 23,005,000 configured source rows | Requires substantial disk, memory, and runtime; run only when resources allow it | performance testing, partition strategy review, capacity planning |

## Smoke Mode

Smoke mode uses the `smoke` profile in `data_sources/config/source_volume.yml`. The current outputs use the latest smoke batch in `data_sources/generated/manifest.json`.

Smoke mode is the recommended default for:

- local test runs
- quality-gate validation
- generated reports
- Streamlit dashboard review
- report generation
- fast reruns before committing changes

## Scale Profile

The scale profile shows how the same source generator can create larger platform volumes:

- Google Ads: 5,000,000 rows
- Facebook Ads: 3,000,000 rows
- TikTok Ads: 2,000,000 rows
- Website Analytics: 10,000,000 rows
- CRM Leads: 2,000,000 rows
- Sales Conversions: 1,000,000 rows
- Marketing Targets: 5,000 rows

The scale figures describe configuration; an executed run is recorded in its generated manifest.

## Recommended Commands

```bash
python3 -B scripts/run_smoke_pipeline.py
python3 -B scripts/load_duckdb_raw.py
python3 -B scripts/build_demo_marts.py
python3 -B scripts/generate_powerbi_handoff.py
python3 -B scripts/build_release_site.py
```

Use `python3 -m pytest -q`, `ruff check .`, and `dbt parse --project-dir dbt --profiles-dir dbt --target duckdb --no-partial-parse` for command-based validation of the tracked project files.

Or run the full local target:

```bash
make demo
```

For a larger local generation run:

```bash
python3 -B data_sources/generate_sources.py --profile dev
```

For scale planning, review:

- `data_sources/config/source_volume.yml`
- `docs/row_count_summary.md`
