# Power BI Semantic Model Package

This folder contains TMDL-style semantic-model assets for the marketing ETL warehouse. It is designed as a source-controlled blueprint for importing exported warehouse tables into Power BI, setting relationships, organizing measures, and building dashboard pages.

Generated files:
- `model.tmdl`: model-level settings.
- `relationships.tmdl`: star-schema relationship definitions.
- `roles.tmdl`: Executive, Channel Manager, and Regional Manager role design; runtime enforcement requires Power BI Desktop or Service validation.
- `tables/*.tmdl`: table, column, and measure definitions.
- `dashboard_pages.yml`: dashboard page blueprint.
- `semantic_model_manifest.json`: generated asset counts.

Dashboard pages:
- **Executive Marketing Overview**: Are marketing dollars producing efficient revenue and margin?
- **Channel Performance**: Which channels are scaling efficiently and which need budget reallocation?
- **Campaign Intelligence**: Which campaigns are wasting budget or driving high-value customers?
- **Funnel Analysis**: Where are leads dropping before revenue conversion?
- **Attribution & ROI**: Why do attribution reports disagree across systems?
- **Target vs Actual**: Are teams meeting regional budget, lead, and revenue targets?
- **Governance & Action Center**: Can leaders trust the dashboard, and who owns the next fixes?
- **GA4 Funnel**: Where does the GA4-style journey drop before purchase?
- **Variance Drivers**: Which diagnostic movements contributed to ROAS and CAC change?
- **Campaign Action Center**: Which transparent actions should marketing leadership prioritize?
- **Scenario Planning**: How do explicit budget, CPC, conversion, AOV, and growth assumptions change planning outcomes?
