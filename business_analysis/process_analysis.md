# Marketing Reporting Process Analysis

## As-Is process

The modeled current state represents a common export-driven reporting workflow. It is not a description of an observed employer process.

```mermaid
flowchart LR
    A["Platform exports"] --> B["Separate spreadsheets"]
    B --> C["Manual KPI calculations"]
    C --> D["Inconsistent attribution"]
    D --> E["Manual investigation"]
    E --> F["Static reporting"]
    F --> G["Slow or disputed decisions"]
```

| Process issue | Analytical consequence | Control gap |
|---|---|---|
| Independent exports | Campaign/source totals drift | No governed reconciliation |
| Spreadsheet formulas | ROAS/CAC definitions vary | No KPI catalog or test |
| Manual campaign mapping | Unmapped records fragment results | No conformed dimensions |
| Late conversions | Historical performance changes silently | No watermarks/incremental handling |
| Ad hoc investigation | Driver logic cannot be reproduced | No deterministic variance or anomaly analysis |
| Static presentation | Exceptions and quality risk are buried | No action center or release gate |

## To-Be process

```mermaid
flowchart LR
    A["Generated sources + live GA4"] --> B["Governed ingestion"]
    B --> C["Contracts, validation, rejected rows"]
    C --> D["Warehouse + dbt"]
    D --> E["Governed KPI layer"]
    E --> F["Variance, anomalies, scenarios"]
    F --> G["Power BI + Streamlit"]
    G --> H["Action center + insight packet"]
    H --> I["Human review"]
    C --> J["Quality hold"]
    J --> I
```

The generated marketing path and live GA4 path remain separate through ingestion and staging, then converge only in governed analytical outputs where their origins are explicit.

## Decision controls

| Stage | Control | Output |
|---|---|---|
| Source | Execution status and source contract | Source assessment, contracts, manifests |
| Landing | Hash, batch, watermark, accepted/rejected counts | Ingestion logs and quality reports |
| Warehouse | Grain, keys, incremental rules | dbt models and tests |
| KPI | Definition, formula, owner, exclusions | KPI catalog and DAX catalog |
| Analysis | Method, baseline, assumptions, limitations | Variance, anomaly, forecast, scenario outputs |
| Recommendation | Rule, supporting metrics, priority, quality override | Action-center marts |
| Reporting | Relationship, filter, usability, acceptance checks | Power BI semantic/page assets and UAT workbook |
| Distribution | Reconciliation and quality gate | Decision-intelligence packet and quality results |

## Expected process outcome

The target process replaces repeated manual reconciliation with reusable checks and traceable outputs. It improves auditability and decision support without assigning unmeasured time savings or business impact.
