# Release Bundle

This folder stores the generated release index for reports, diagrams, monitoring outputs, semantic metadata, and validation manifests.

Generate:

```bash
python3 -B scripts/generate_release_bundle.py
python3 -B scripts/build_release_site.py
```

Outputs:

- `release/generated/release_manifest.json`
- `release/generated/release_summary.md`
- `release/generated/release_index.html`
- `release/site/index.html`
- `release/site/site_manifest.json`
