# Ad-Hoc Marketing Analysis Pack

Six modeled stakeholder requests demonstrate how an ambiguous business question becomes a controlled, reproducible analysis and a concise recommendation.

All marketing business data is generated/synthetic. The bounded real portfolio-site GA4 path is separate and is not used in these analyses. Findings are descriptive; attribution and scenario outputs do not establish causal lift.

| Request | Modeled requester | Decision question | Start here |
|---|---|---|---|
| REQ-01 | VP Marketing | Why is paid-social attributed ROAS below the review line? | [ROAS review](request_01_roas_decline/request.md) |
| REQ-02 | Sales Operations Manager | Where is the largest funnel leakage? | [Funnel leakage](request_02_funnel_leakage/request.md) |
| REQ-03 | Finance Business Partner | Why did revenue miss target with spend near plan? | [Target miss](request_03_target_miss/request.md) |
| REQ-04 | Marketing Analytics Manager | Does attribution methodology change the conclusion? | [Attribution sensitivity](request_04_attribution_sensitivity/request.md) |
| REQ-05 | Performance Marketing Manager | What should be reviewed before reallocating budget? | [SIMULATED scenario](request_05_budget_scenario/request.md) |
| REQ-06 | Marketing Analytics Manager | Can recommendations be trusted? | [Quality hold](request_06_data_quality_investigation/request.md) |

## Reproduce

```bash
python3 -B analytics_requests/build_analysis_pack.py
```

The builder loads the committed, generated mart snapshot in `canonical_input/` into an in-memory DuckDB database, reads the canonical scenario snapshot at `canonical_input/mart_budget_scenarios.csv`, and regenerates each `result.csv`, `chart.png`, `request.md`, `response_memo.md`, and `validation.json`. The scenario snapshot originates from the deterministic budget-funnel methodology, but the committed canonical CSV is the file consumed during P2 2.0 analysis generation. This makes the published analysis independent of ignored local warehouses and shell environment variables. `manifest.yml` records request metadata and calculated summary values.

## Analysis contract

Every request separates observation, interpretation, business meaning, recommendation, and limitations. `validation.json` records input hashes, output schema, row count, result hash, and request-specific checks.
