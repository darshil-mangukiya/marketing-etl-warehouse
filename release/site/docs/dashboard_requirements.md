# Dashboard Requirements

## 1. Executive Marketing Overview

| Requirement | Detail |
|---|---|
| Business question | Is marketing performance on plan and supported by fresh, trusted data? |
| Primary stakeholders | CMO / VP Marketing, Executive Leadership, Finance Manager |
| KPIs | Spend, booked revenue, gross margin, ROAS, CAC, target attainment, source health |
| Filters | Reporting month, channel, region, owner team |
| Drilldowns | Channel to campaign, month to source health, target variance to region/channel |
| Data sources | paid media, sales conversions, targets, source health |
| Mart/model used | `mart_executive_scorecard`, `mart_channel_performance`, `mart_target_vs_actual`, `mart_source_health` |
| Acceptance criteria | KPI totals reconcile to exported marts; source health and data provenance are visible. |
| Data quality warnings | Stale sources, rejected rows, missing attribution, unmapped campaigns |

## 2. Channel Performance

| Requirement | Detail |
|---|---|
| Business question | Which channels should receive more or less budget? |
| Primary stakeholders | CMO / VP Marketing, Growth Marketing Manager |
| KPIs | Spend, clicks, leads, conversions, booked revenue, gross margin, ROAS, CAC |
| Filters | Month, channel group, device, region |
| Drilldowns | Channel to campaign to region/device |
| Data sources | paid media, website analytics, CRM leads, sales conversions |
| Mart/model used | `mart_channel_performance` |
| Acceptance criteria | Channel totals reconcile to mart exports and KPI formulas match catalog definitions. |
| Data quality warnings | Missing attribution, stale paid media source, rejected source rows |

## 3. Campaign Intelligence

| Requirement | Detail |
|---|---|
| Business question | Which campaigns are wasting budget or driving high-value customers? |
| Primary stakeholders | Growth Marketing Manager, BI Developer |
| KPIs | Campaign spend, conversions, attributed revenue, attributed ROAS, waste flag |
| Filters | Campaign, channel, owner team, waste budget flag |
| Drilldowns | Campaign to source records and quality exceptions |
| Data sources | paid media, campaign mappings, attribution outputs |
| Mart/model used | `mart_campaign_performance`, `mart_campaign_optimization` |
| Acceptance criteria | Waste flags and recommendations are visible; unmapped campaigns are not hidden. |
| Data quality warnings | Duplicate campaign IDs, missing campaign mappings, missing attribution IDs |

## 4. Funnel Analysis

| Requirement | Detail |
|---|---|
| Business question | Where are leads dropping before revenue conversion? |
| Primary stakeholders | Sales Operations Manager, Growth Marketing Manager |
| KPIs | Leads, MQLs, SQLs, conversions, lead-to-MQL rate, SQL-to-close rate |
| Filters | Month, channel, region, sales rep |
| Drilldowns | Source to funnel stage to campaign |
| Data sources | website analytics, CRM leads, sales conversions |
| Mart/model used | `mart_funnel_performance` |
| Acceptance criteria | Funnel rates calculate from prior stage counts and reconcile to mart totals. |
| Data quality warnings | Orphan conversions, missing lead IDs, incomplete CRM stage data |

## 5. Attribution and ROI

| Requirement | Detail |
|---|---|
| Business question | Why do attribution reports disagree across systems? |
| Primary stakeholders | CMO / VP Marketing, Analytics Engineer, BI Developer |
| KPIs | First-touch revenue, last-touch revenue, linear revenue, weighted conversions, attribution coverage |
| Filters | Month, campaign, channel, attribution model |
| Drilldowns | Attribution model to touchpoint to conversion |
| Data sources | paid media, website analytics, CRM leads, sales conversions |
| Mart/model used | `fact_attribution`, `mart_attribution_summary`, `mart_attribution_model_comparison` |
| Acceptance criteria | Attribution model assumptions are visible and revenue totals reconcile by model. |
| Data quality warnings | Missing attribution IDs, late conversions, unmatched journeys |

## 6. Target vs Actual

| Requirement | Detail |
|---|---|
| Business question | Are teams meeting monthly budget, lead, and revenue targets? |
| Primary stakeholders | Finance Manager, CMO / VP Marketing |
| KPIs | Target spend, actual spend, target revenue, actual revenue, spend attainment, revenue attainment, lead attainment |
| Filters | Target month, region, channel, budget owner |
| Drilldowns | Region to channel to campaign |
| Data sources | marketing targets, paid media, sales conversions, CRM leads |
| Mart/model used | `mart_target_vs_actual`, `mart_budget_pacing` |
| Acceptance criteria | Target and actual values align to the same month/channel grain. |
| Data quality warnings | Missing target mappings, null regions, stale target files |

## 7. Data Quality and Monitoring

| Requirement | Detail |
|---|---|
| Business question | Can reporting data be trusted for review? |
| Primary stakeholders | Data Engineer, BI Developer, Analytics Engineer, Executive Leadership |
| KPIs | rejected rows, rejection rate, source health, failed quality files, data product score |
| Filters | Source system, rule, severity, batch ID, status |
| Drilldowns | Source system to rule to rejected records |
| Data sources | ingestion audit, validation reports, quality checks, source health |
| Mart/model used | `mart_data_quality_monitoring`, `mart_source_health`, `mart_data_product_scorecard` |
| Acceptance criteria | Quality failures are visible with source, file, and rule context before reporting signoff. |
| Data quality warnings | stale data, schema drift, invalid KPI relationships, rejected records |
