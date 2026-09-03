# Local Quality Gate

This is the local CI path for the local data platform.

```bash
python3 -B local_ci/local_quality_gate.py
```

It runs:

- smoke pipeline
- Great Expectations-compatible checkpoint
- contract validation
- demo mart generation
- catalog and lineage generation
- release asset generation
- pytest suite
- dbt parse

The result is written to `local_ci/latest_quality_gate.json`.
