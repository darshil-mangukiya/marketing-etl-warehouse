# Relationship Strategy


Relationships use stable text/date keys, many-to-one cardinality from facts/marts to dimensions, and single-direction filtering to prevent ambiguous filter paths.

Recommended direction: dimensions filter facts and reporting marts. Avoid bidirectional filters unless a specific drill-through or bridge-table use case is validated. Keep inactive relationships documented if future date roles are added.


These BI documents complement the completed dashboard file committed at `dashboards/powerbi/p2_marketing_performance_dashboard.pbix`; rebuild guidance lives in `dashboards/powerbi/BUILD_CHECKLIST.md`.
