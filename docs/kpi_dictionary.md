# KPI Dictionary Index and Upgrade Addendum

Canonical original formulas live in `semantic/kpi_catalog.yml`, `semantic_layer/kpi_catalog.md` and the DAX catalogs. The upgrade does not redefine them.

| KPI | Governed formula | Notes |
|---|---|---|
| ROAS | revenue / spend | Use booked or attributed revenue exactly as labeled; never mix silently |
| CAC | spend / closed-won conversions | Null when denominator is zero |
| CTR | clicks / impressions | Null when impressions are zero |
| CPC | spend / clicks | Null when clicks are zero |
| Conversion rate | conversions / governed funnel denominator | Visual must label denominator |
| AOV | revenue / conversions | Used as a diagnostic contributor |
| Target attainment | actual / target | Missing target is distinct from zero target |
| Absolute variance | current - prior | Same grain and complete periods required |
| Percentage variance | (current - prior) / prior | Null when prior is zero |

`primary_driver`, severity and recommended actions are governed rules, not KPIs and not AI/causal results.
