# DAX Audit and Optimization

## Result

All 59 source-controlled measures were reviewed. Zero measures changed because no semantic correction or defensible optimization was required. Additive measures already use direct aggregation; ratios branch from base measures and use `DIVIDE`; scenario target variances branch from scenario measures; technical columns remain outside measure logic. This is **SOURCE-CONTROLLED / STATICALLY VALIDATED**. Power BI Performance Analyzer was not executed.

## Measure hierarchy

| Layer | Representative project measures |
|---|---|
| Base | Total Spend, Booked Revenue, Gross Margin, Total Clicks, Total Impressions, Total Leads, Closed Won Conversions |
| Derived efficiency | ROAS, Marketing Efficiency Ratio, Click Through Rate, Cost Per Lead, CAC, Attributed ROAS |
| Funnel | Funnel Leads, Funnel MQLs, Funnel SQLs, Lead to MQL Rate, SQL to Close Rate, GA4 Session to Purchase Rate |
| Target / variance | Target Revenue, Actual Revenue, Revenue Attainment, Target Spend, Actual Spend, Spend Attainment, ROAS Absolute Variance |
| Scenario | Scenario Budget, Scenario Projected Revenue, Scenario Projected Customers, Scenario ROAS, Scenario CAC, target variances |
| Quality / decision | Open Actions, P0 Actions, P1 Actions, Data Quality Holds, Average Data Product Score, Governance Risk Count |

## Audit decisions

| Measure/pattern reviewed | Issue found | Decision | Rationale | Validation | Semantic impact |
|---|---|---|---|---|---|
| Ratio measures | Divide-by-zero risk | Retain `DIVIDE` | Already defensive and branches from governed totals | Static expression tests | None |
| Scenario ROAS/CAC | Repeated numerator/denominator risk | Retain measure branching | Uses scenario revenue/budget/customer base measures | BI validation + pytest | None |
| Scenario target variance | Target context ambiguity | Retain `MAX(target)` under scenario filter | One governed target per scenario row set | Scenario contract tests | None |
| Action counts | Filter context | Retain `CALCULATE` predicates | Explicit priority/action filters are readable | Static role/measure validation | None |
| Attribution measures | Potential iterator overhead | Retain direct `SUM` | No row iterator or duplicated filter scan exists | Semantic manifest validation | None |
| Time intelligence | No governed prior-period DAX measures in current package | Do not invent measures | Period variance is calculated in the governed dbt mart | dbt build/tests | None |

No calculated column was introduced, no `FILTER` iterator misuse was found, and no `ALL`/`ALLSELECTED` behavior required correction. Runtime visual timings remain **NOT EXECUTED**.
