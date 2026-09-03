# Business Case

## Business Problem

A SaaS/ecommerce company runs paid media, website, CRM, and sales operations across disconnected systems. Marketing reports are built manually from exports, causing inconsistent attribution, delayed reporting, broken dashboards, and budget decisions based on incomplete data.

This project builds a governed marketing data platform that automates ingestion, standardizes source data, models campaign and funnel performance, and publishes executive-ready BI datasets.

## Stakeholder Pain

Marketing leaders cannot confidently answer which campaigns deserve more budget, which channels waste spend, where leads drop off, or why platform reports disagree. Analysts spend time fixing spreadsheets instead of explaining performance.

## Before And After

| Before | After |
|---|---|
| Manual exports from ad, web, CRM, and sales tools | Automated API and file ingestion |
| Inconsistent campaign names and source IDs | Normalized campaign, channel, source, region, and device mappings |
| Late conversions break ROI reporting | Watermark tracking and late-arriving conversion handling |
| KPI logic scattered across spreadsheets | Reusable reporting marts and semantic KPI definitions |
| Limited trust in dashboard numbers | Data quality checks, rejected-row outputs, and source health monitoring |

## Executive Decisions Supported

| Decision | Dataset/Dashboard |
|---|---|
| Reallocate monthly ad budget | Channel performance, budget efficiency |
| Pause underperforming campaigns | Campaign intelligence |
| Fix broken campaign mapping | Data quality monitoring |
| Invest in high-LTV channels | Customer value mart |
| Improve lead handoff | Funnel performance |
| Explain attribution mismatch | Attribution summary |
| Review source reliability | Source health monitoring |
| Approve monthly marketing plan | Target vs actual |

## Sample Business Insights

These example insights come from generated project scenarios; they do not represent company performance.

- TikTok has low CAC but weaker closed-won conversion, showing that cheap lead volume does not always mean high customer quality.
- Google Ads has higher CPC but stronger revenue per conversion, making it a better candidate for budget scaling.
- Facebook produces many top-of-funnel leads but a lower SQL rate, indicating funnel quality or targeting issues.
- Around 12 percent of conversions arrive late, making incremental processing and attribution windows necessary.
- Several campaigns spend budget without mapped attribution IDs, creating reporting gaps and unreliable ROI.
- Mobile traffic converts well at the session level but drops during lead qualification, suggesting a mobile funnel quality issue.
- The West region beats target while the East region misses pipeline goals, supporting regional budget reallocation.
- Budget pacing flags overspend before month-end, allowing marketing leaders to correct spend earlier.
