# Power BI PBIP Scaffold

This folder is a source-controlled Power BI Project scaffold that pairs with the generated TMDL-style semantic assets in `semantic_layer/powerbi_tmdl/`.

It is intentionally lightweight because the project does not require a checked-in `.pbix` binary. The purpose is to show how the exported warehouse tables, certified measures, relationships, and dashboard pages would be organized in a professional Power BI workflow.

## Suggested Build Flow

1. Run `python3 -B scripts/build_demo_marts.py`.
2. Run `python3 -B scripts/generate_powerbi_semantic_model.py`.
3. Import CSV exports from `data/exports/` or warehouse exports from PostgreSQL.
4. Recreate relationships from `semantic_layer/powerbi_tmdl/relationships.tmdl`.
5. Recreate measures from `semantic_layer/powerbi_tmdl/tables/*.tmdl` and `semantic_layer/dax_measure_catalog.md`.
6. Build pages from `semantic_layer/powerbi_tmdl/dashboard_pages.yml`.
7. Use `docs/dashboard_outputs.md` and `reports/generated/governance_release_packet.html` before certifying the report.
8. Use `reports/generated/governance_release_packet.html` as the release certification evidence.

## Files

- `MarketingPlatform.pbip`: Power BI project pointer scaffold.
- `definition/report.json`: report metadata scaffold.
- `definition/pages.json`: expected page inventory.
- `semanticModel/README.md`: semantic model build notes.

The generated TMDL package remains the source of truth for measures and relationships.
