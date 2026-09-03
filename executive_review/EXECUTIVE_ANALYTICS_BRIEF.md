# Executive Analytics Brief

All marketing business performance data below is generated/synthetic. This is a modeled portfolio case study, not an account of actual stakeholder decisions or live advertising activity.

## What happened?

- Paid social shows **$1.20M spend**, **$34.4K attributed revenue**, and **0.03x attributed ROAS** in the latest available governed campaign period.
- **303 of 385 paid-social leads (78.7%)** do not reach MQL; this is the largest internally consistent funnel loss.
- The selected LATAM Paid Search target record reached **107.3% spend attainment**, but only **14.6% attributed-revenue attainment** and **1.8% lead attainment**.
- Paid Search ranks first under all six attribution methods, while allocated revenue ranges from **$119.3K to $123.2K**.
- Three paid-media sources require a release hold because they have error-severity quality failures and rejected rows; four other sources require review, and the campaign-level rule emits one automatic hold.

## Why?

- Paid-social weak return is distributed across campaigns: the two largest break-even shortfalls represent only **24.0%** of the total.
- Funnel loss is concentrated before MQL qualification, which is associated with lead-source mix, scoring, or qualification definitions rather than only close-stage execution.
- Revenue, lead, and platform-conversion attainment conflict in the target record, indicating a definition, attribution, join, or target-grain issue.
- Attribution weights change allocated value, but not the leading channel in this generated dataset.

## So what?

The performance signal warrants investigation, but the source failures and metric conflicts make a budget recommendation unsafe to release. Treating the current numbers as a clean efficiency story would overstate reporting trust.

## Recommended actions

1. Apply a manual **DATA QUALITY HOLD** to paid-media-dependent recommendations.
2. Resolve or formally accept the failed source-contract results and rerun monitoring.
3. Reconcile platform conversions to leads, attributed revenue, campaign mapping, and target grain.
4. Review paid-social campaign diagnostics and lead-to-MQL qualification after data controls pass.
5. Present attribution as a six-method sensitivity range; do not describe it as causal lift.

## Risks / limitations

- Marketing business data is generated/synthetic; no real customers, spend, performance, or realized impact is claimed.
- The bounded real portfolio-site GA4 path is separate and unused in this review.
- Attribution redistributes observed revenue and does not establish incrementality.
- Budget outputs are deterministic **SIMULATED / WHAT-IF** scenarios, not forecasts or optimal allocations.
- Some marts expose cross-period cohort timing and channel-key reconciliation limitations; the analyses preserve grain and call these out rather than forcing a false conclusion.

## Evidence

- `analytics_requests/request_01_roas_decline/result.csv`
- `analytics_requests/request_02_funnel_leakage/result.csv`
- `analytics_requests/request_03_target_miss/result.csv`
- `analytics_requests/request_04_attribution_sensitivity/result.csv`
- `analytics_requests/request_05_budget_scenario/result.csv`
- `analytics_requests/request_06_data_quality_investigation/result.csv`
- `analytics_requests/canonical_input/`
