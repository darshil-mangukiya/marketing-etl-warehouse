# Build Checklist

1. Open Power BI Desktop.
2. Get Data > Folder > select `dashboards/powerbi/data/`.
3. Load each CSV as a separate table.
4. Set key columns to Text, date columns to Date, and metric columns to Decimal Number or Whole Number.
5. Create a Measures table.
6. Paste all measures from `dax_measures.dax`.
7. Create the relationships in `relationship_map.md` with single-direction filtering.
8. Build seven pages: Executive Marketing Overview, Channel Performance, Campaign ROI Deep Dive, Funnel Conversion, Budget Pacing & Targets, Attribution & Customer Value, and Data Quality & Refresh Health.
9. Add slicers for date, channel, campaign, region, device/platform where available, and customer segment.
10. Add campaign drill-through, a tooltip page, and conditional formatting for ROAS, pacing, data quality, and action priority.
11. Capture screenshots listed in `screenshots/SHOT_LIST.md`.
12. Save as `p2_marketing_performance_dashboard.pbix` and export PDF from Power BI Desktop if needed. The completed dashboard file is committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`.
