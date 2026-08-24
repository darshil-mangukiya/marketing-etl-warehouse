# Governance Artifacts

This folder contains generated governance outputs for the marketing ETL and BI data product.

Generate:

```bash
python3 -B scripts/generate_governance_pack.py
```

Outputs are written to `governance/generated/` and include:

- data classification catalog
- access policy matrix
- retention policy matrix
- BI release certification evidence
- governance manifest

The HTML release packet is written to `reports/generated/governance_release_packet.html`.
