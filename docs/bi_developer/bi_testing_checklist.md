# Bi Testing Checklist


1. Validate all expected CSV tables load.
2. Validate date and numeric data types.
3. Validate relationship cardinality and filter direction.
4. Reconcile Total Spend, Revenue, ROAS, CAC, and target attainment to CSV mart totals.
5. Validate slicer behavior across all pages.
6. Validate campaign drill-through.
7. Validate tooltip context.
8. Validate action priority conditional formatting.
9. Validate source-health caveats are visible.
10. Validate each page identifies data provenance and analytical output boundaries.
11. Validate the committed `.pbix` and screenshots match the documented dashboard pages and file paths.
12. Validate the report can refresh after moving the folder path.


These BI documents complement the completed dashboard file committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`; rebuild guidance lives in `dashboards/powerbi/BUILD_CHECKLIST.md`.
