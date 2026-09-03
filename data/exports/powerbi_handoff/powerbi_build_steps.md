# Power BI Build Steps

1. Open Power BI Desktop.
2. Select Get Data > Folder and choose `data/exports/powerbi_handoff/`.
3. Load each CSV as a separate table.
4. Set date fields to Date, metric fields to Decimal Number or Whole Number, and keys to Text.
5. Create relationships from `relationships.md` with single-direction filters.
6. Create a Measures table and paste measures from `dax_measures.md`.
7. Preserve the seven evidenced PBIX pages and assemble the Power BI-ready analytical pages from `page_specs.md`.
8. Refresh screenshot evidence from `screenshot_checklist.md`.
9. Save the editable report as `p2_marketing_performance_dashboard.pbix`.
