# BI Release Certification and Governance Packet

Generated: `2026-08-22T22:35:29.704493+00:00`

Release status: `certified`

| Control | Value |
|---|---:|
| Artifact Pass Rate | 100% |
| Demo Mart Count | 28 |
| Semantic Table Count | 17 |
| Semantic Measure Count | 59 |
| Classified Assets | 10 |
| Restricted or Confidential Assets | 6 |
| Direct-Identifier Assets | 3 |
| Access Policy Rows | 21 |
| Retention Policies | 9 |

## Required Artifacts

- [x] `data/exports/demo_mart_manifest.json` (4,065 bytes)
- [x] `data/exports/demo_mart_data_product_scorecard.csv` (2,121 bytes)
- [x] `data/exports/demo_mart_semantic_kpi_governance.csv` (4,002 bytes)
- [x] `data/exports/demo_mart_action_center.csv` (9,584 bytes)
- [x] `reports/generated/executive_planning_report.html` (14,978 bytes)
- [x] `semantic_layer/powerbi_tmdl/semantic_model_manifest.json` (205 bytes)
- [x] `docs/data_quality_framework.md` (2,518 bytes)
- [x] `docs/dashboard_outputs.md` (3,734 bytes)

## Privacy Controls

- Direct identifiers are restricted to data engineering, analytics engineering, sales operations, revenue operations, or finance depending on business need.
- BI and leadership surfaces consume masked, surrogate-keyed, or aggregate marts.
- Customer-level exports are restricted; executive dashboards should use channel, segment, region, or product rollups.
- External audit sharing uses redacted aggregate evidence only.

## Release Decision

The release is marked `certified` when all required data, dashboard, semantic, governance, and documentation artifacts exist.
