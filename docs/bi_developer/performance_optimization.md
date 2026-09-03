# Performance Optimization


Use import mode, hide keys after relationship setup, avoid bidirectional filters, prefer measures to calculated columns, aggregate at mart grain before visual rendering, and disable auto date/time when a real date table is used.

For larger scale profiles, use aggregation tables, incremental refresh policies, and source-side transformations in the warehouse instead of heavy Power Query logic.


These BI documents complement the completed dashboard file committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`; rebuild guidance lives in `dashboards/powerbi/BUILD_CHECKLIST.md`.
