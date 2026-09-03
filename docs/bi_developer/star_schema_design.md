# Star Schema Design


The warehouse uses reusable fact tables for campaign performance, sessions, leads, conversions, revenue, targets, and attribution. Conformed dimensions include date, campaign, channel, customer, region, device, product, sales rep, and source system.

Fact grain is kept explicit: campaign performance is campaign-date-channel, funnel performance is reporting month and channel, target performance is month-region-channel, and attribution is campaign/model/date where available. Dimension grain is one row per business key, with campaign handling documented as SCD-style because campaign names and mappings can change over time.


These BI documents complement the completed dashboard file committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`; rebuild guidance lives in `dashboards/powerbi/BUILD_CHECKLIST.md`.
