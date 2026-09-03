# Executive Insights Summary

## Executive Summary

The generated insights summarize channel efficiency, campaign ROI, high-spend low-return risk, funnel drop-off, budget pacing, target attainment, attribution differences, customer value, source/data quality, and recommended next actions.

## Top 5 Insights

- **Direct leads channel efficiency** (P1): Highest observed channel ROAS is 0.00x; weakest channel ROAS is 0.00x. Recommended action: Review budget shift from weak to efficient channels.
- **High-spend low-return campaigns need review** (P0): 29 campaigns spend above the median while attributed ROAS is below 1.0x. Recommended action: Use the campaign action recommendation output to decide pause, monitor, or reallocation.
- **SQL-to-close is the funnel stage to inspect** (P1): Weakest SQL-to-close rate is 33.3%. Recommended action: Review sales handoff and lead quality for low-close segments.
- **Target attainment is below plan** (P1): Average revenue attainment is 0.0%; average spend attainment is 1892.6%. Recommended action: Separate budget under-pacing from performance under-delivery before reallocating spend.
- **Attribution model choice changes ROI interpretation** (P2): Attribution comparison marts show variance between model outputs. Recommended action: Use attribution page notes when presenting campaign ROI to stakeholders.

## Risks To Review

- Direct leads channel efficiency: Highest observed channel ROAS is 0.00x; weakest channel ROAS is 0.00x.
- High-spend low-return campaigns need review: 29 campaigns spend above the median while attributed ROAS is below 1.0x.
- SQL-to-close is the funnel stage to inspect: Weakest SQL-to-close rate is 33.3%.
- Target attainment is below plan: Average revenue attainment is 0.0%; average spend attainment is 1892.6%.
- Data-quality caveats should stay visible: Validation outputs include 43 rejected rows in the current demo evidence.

## Opportunities To Scale

- Review campaigns marked `Scale` in `data/exports/analyst_outputs/campaign_action_recommendations.csv`.
- Compare channel ROAS and CAC before moving budget.

## Data-Quality Caveats

- Generated project data keeps the workflow reproducible without customer records.
- Recommendations are designed as analyst decision support; budget automation is a deployment extension.

## Recommended 30/60/90-Day Actions

- 30 days: validate campaign action logic with stakeholders and confirm KPI definitions.
- 60 days: review the committed Power BI Desktop report and refresh screenshots after model changes.
- 90 days: extend the pattern with managed API connectors or cloud warehouse deployment when needed.
