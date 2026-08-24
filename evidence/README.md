# Visualization Assets

Generate static architecture and dashboard visuals from the local smoke profile:

```bash
python3 -B scripts/generate_release_evidence.py
```

Generated outputs:

- `evidence/generated/architecture_snapshot.svg`
- `evidence/generated/dashboard_wireframe.svg`
- `evidence/generated/dashboard_executive_preview.svg`
- `evidence/generated/dashboard_governance_preview.svg`
- `evidence/generated/dashboard_observability_preview.svg`
- `evidence/generated/evidence_manifest.json`

The local release bundle and static site consume these assets.
