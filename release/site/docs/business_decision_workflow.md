# Business Decision Workflow

## 1. Weekly Marketing Performance Review

| Workflow Element | Detail |
|---|---|
| Trigger | Weekly performance meeting or campaign spend review |
| Stakeholders | CMO / VP Marketing, Growth Marketing Manager, Finance Manager |
| Inputs | Channel performance, campaign performance, executive scorecard, source health |
| Dashboards/marts used | `mart_channel_performance`, `mart_campaign_performance`, `mart_source_health` |
| Decision made | Scale, maintain, reduce, or investigate channel/campaign spend |
| Follow-up action | Update campaign budget recommendation and owner action list |
| Data quality checks required | freshness status, missing attribution, rejected paid media rows |

## 2. Monthly Budget Planning

| Workflow Element | Detail |
|---|---|
| Trigger | Month-end close or next-month budget allocation cycle |
| Stakeholders | Finance Manager, CMO / VP Marketing, Executive Leadership |
| Inputs | Target vs actual, budget pacing, revenue, margin, forecast-style planning outputs |
| Dashboards/marts used | `mart_target_vs_actual`, `mart_budget_pacing`, `mart_performance_forecast` |
| Decision made | Approve, hold, or reallocate monthly channel budgets |
| Follow-up action | Document variance drivers and update budget owner actions |
| Data quality checks required | target grain alignment, source freshness, sales conversion completeness |

## 3. Campaign Optimization Workflow

| Workflow Element | Detail |
|---|---|
| Trigger | Campaign waste flag, low attributed ROAS, or high spend without conversion |
| Stakeholders | Growth Marketing Manager, BI Developer, Analytics Engineer |
| Inputs | Campaign intelligence, optimization recommendations, attribution summary |
| Dashboards/marts used | `mart_campaign_optimization`, `mart_campaign_performance`, `mart_attribution_summary` |
| Decision made | Pause, fix, maintain, or scale campaign |
| Follow-up action | Resolve mapping issues, adjust targeting, or update budget shift recommendation |
| Data quality checks required | campaign mapping, attribution ID coverage, duplicate campaign IDs |

## 4. Funnel Quality Review

| Workflow Element | Detail |
|---|---|
| Trigger | Lead volume increases without matching SQL or closed-won conversion growth |
| Stakeholders | Sales Operations Manager, Growth Marketing Manager |
| Inputs | Funnel performance, customer value, conversion lag |
| Dashboards/marts used | `mart_funnel_performance`, `mart_customer_value`, `mart_conversion_lag` |
| Decision made | Improve lead handoff, revise qualification rules, or adjust source targeting |
| Follow-up action | Assign sales operations action and monitor stage conversion in next cycle |
| Data quality checks required | CRM stage completeness, orphan conversions, lead/source mappings |

## 5. Data Quality Exception Review

| Workflow Element | Detail |
|---|---|
| Trigger | Source health watch/fail status, rejected-row spike, stale source, or missing mappings |
| Stakeholders | Data Engineer, BI Developer, Analytics Engineer, Executive Leadership for high-impact issues |
| Inputs | Source health, data quality monitoring, rejected records, governance packet |
| Dashboards/marts used | `mart_source_health`, `mart_data_quality_monitoring`, `mart_data_product_scorecard` |
| Decision made | Continue reporting, publish with caveat, or block executive reporting until corrected |
| Follow-up action | Assign owner, fix source or mapping issue, rerun the pipeline, and refresh outputs |
| Data quality checks required | source freshness, schema drift, rejected records, KPI relationship failures |
