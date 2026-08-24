# Dashboard Measure Matrix

| Dashboard Page | Primary Measures | Grain | Drilldowns | Owner |
|---|---|---|---|---|
| Executive Marketing Overview | Total Spend, Booked Revenue, Gross Margin, ROAS, CAC, MER | Month, channel | Channel, region, campaign owner | VP Marketing |
| Channel Performance | Spend, Leads, Closed Won Conversions, CPL, CAC, ROAS | Month, channel | Device, region, campaign | Growth Lead |
| Campaign Intelligence | Campaign Spend, Attributed Revenue, Attributed ROAS, Waste Campaigns | Campaign | Campaign owner, platform, budget flag | Performance Marketing |
| Funnel Analysis | Funnel Leads, MQLs, SQLs, Lead-to-MQL Rate, SQL-to-Close Rate | Month, channel | Sales rep, region, qualification stage | Revenue Operations |
| Attribution & ROI | First Touch Revenue, Last Touch Revenue, Linear Revenue, Time Decay Revenue, Revenue Delta | Month, campaign, model | Campaign, channel, attribution model | Analytics Engineering |
| Target vs Actual | Target Revenue, Actual Revenue, Revenue Attainment, Target Spend, Actual Spend | Month, region, channel | Budget owner, territory | Finance + Marketing Ops |
| Governance & Action Center | Average Data Product Score, At Risk Domains, Open Actions, P0 Actions, Certified KPIs | Scorecard domain, owner, action priority | Domain, owner team, action type, KPI certification | Data Product Owner |
| Data Quality & Monitoring | Rejected Rows, Failed Files, Freshness Status, Contract Status, Source Health | Batch, source system | File, rule, severity | Data Platform |

## Measure Design Rules

- Measures use explicit `DIVIDE` logic to avoid broken visuals from zero denominators.
- Additive measures are aggregated from marts; ratios are recalculated as measures.
- Operational metrics remain visible in a monitoring page, not mixed into executive ROI pages.
- Attribution measures must display the selected attribution model or comparison label.
