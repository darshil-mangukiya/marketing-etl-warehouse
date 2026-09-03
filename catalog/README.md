# Catalog and Lineage

Generate local catalog artifacts:

```bash
python3 -B scripts/generate_catalog.py
```

Outputs:

- `catalog/generated/data_catalog.json`
- `catalog/generated/lineage_edges.csv`
- `catalog/generated/bi_field_dictionary.csv`
- `catalog/generated/lineage_diagram.md`

These are lightweight, local equivalents of data catalog and lineage artifacts used in production platforms.
