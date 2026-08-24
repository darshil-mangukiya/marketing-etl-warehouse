# dbt Lineage

```mermaid
flowchart LR
    RAW["raw sources"] --> STG["staging models"]
    STG --> INT1["int_campaign_spend_unified"]
    STG --> INT2["int_customer_journey"]
    STG --> INT3["int_attribution_touchpoints"]
    INT1 --> FACTCAMPAIGN["fact_campaign_performance"]
    INT2 --> DIMCUSTOMER["dim_customer"]
    INT3 --> FACTATTR["fact_attribution"]
    STG --> DIMS["conformed dimensions"]
    STG --> FACTS["sessions, leads, conversions, revenue, targets"]
    FACTS --> MARTS["reporting marts"]
    FACTCAMPAIGN --> MARTS
    FACTATTR --> MARTS
    DIMS --> MARTS
```

## Model Layers

- `staging`: type casting, naming, source-specific cleanup, channel normalization, CDC delete filtering.
- `intermediate`: cross-source unions, journey stitching, attribution touchpoint eligibility.
- `marts/core`: dimensional warehouse facts and dimensions.
- `marts/reporting`: business-ready datasets for executive and analyst dashboards.

## dbt Tests

- Required source fields and accepted values.
- Unique/not-null warehouse keys where appropriate.
- Custom KPI relationship assertion for impossible campaign metrics.
- Source freshness definitions for raw tables.
