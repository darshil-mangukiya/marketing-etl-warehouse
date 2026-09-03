# Acceptance Criteria


1. Project documentation identifies the source of generated and live data paths.
2. `make analyst-outputs` generates campaign action recommendations and executive insights.
3. Campaign recommendations include action, priority, and reason fields.
4. Executive insights include category, title, detail, evidence metric, recommended action, and priority.
5. `data/exports/powerbi_handoff/` includes import-ready CSV tables and handoff documentation.
6. The role-based demo guide covers Data Analyst, Business Analyst, and BI Developer paths.
7. Business docs include stakeholder matrix, user stories, UAT plan, acceptance criteria, dashboard requirements, KPI governance, source-to-target mapping, and decision workflows.
8. BI docs explain fact grain, dimension grain, relationships, measure table strategy, slicers, tooltips, refresh, performance, RLS, and testing.
9. Public evidence counts are verified from tracked project files, tests, and dashboard artifacts.
10. Tests verify key generated assets and prevent claiming a built Power BI dashboard when `.pbix` is absent.


Acceptance criteria are evaluated against generated, privacy-safe source profiles and the tracked local review artifacts.
