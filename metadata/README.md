# Metadata Exports

This folder contains metadata-platform scaffolding for the marketing warehouse project.

Run:

```bash
python3 -B scripts/generate_lineage_metadata.py
```

Generated outputs land in `metadata/generated/`:

- `openlineage_events.jsonl`: OpenLineage-style run events for source and dbt lineage.
- `datahub_mces.json`: DataHub-style metadata change events for datasets and BI assets.
- `lineage_manifest.json`: summary counts and output paths.
- `lineage_summary.md`: human-readable lineage summary for the generated release bundle.
