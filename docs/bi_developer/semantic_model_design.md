# Semantic Model Design


The semantic model favors import-mode star-schema tables, a dedicated measure table, governed DAX, and single-direction relationships from dimensions into facts/marts.

The Power BI handoff package separates import tables, relationship documentation, DAX measures, page specs, Power Query notes, and screenshot checklist so a BI developer can build the `.pbix` manually without guessing the model.


These BI documents complement the completed dashboard file committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`; rebuild guidance lives in `dashboards/powerbi/BUILD_CHECKLIST.md`.
