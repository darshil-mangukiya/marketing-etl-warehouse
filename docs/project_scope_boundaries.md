# Project Scope and Boundaries

This project is designed as a local-first marketing analytics platform. Generated source profiles keep local execution reproducible without customer or advertising-account records.

| Area | Scope |
|---|---|
| Source data | Records are generated for repeatable execution and do not contain customer, advertising-account, CRM, or sales-system records. |
| Local stack | The repository mirrors cloud data-platform patterns through Docker/PostgreSQL, dbt, local lake folders, generated evidence, and repeatable tests. |
| Smoke profile | Smaller default row counts support fast laptop review. |
| Scale profile | Larger datasets can be generated locally and recorded in a matching run manifest. |
| Attribution | Attribution logic is transparent and practical for reporting review; deeper incrementality and causal modeling are deployment extensions. |
| Power BI Desktop | The committed `.pbix`, screenshots, semantic docs, and handoff assets support local BI review and extension. |
| API simulator | The simulator represents vendor-like API behavior for ingestion testing and local validation. |
| Local secrets | Environment examples document configuration shape; managed secret stores are a deployment extension. |

## Technical Boundary

The repository demonstrates ingestion, orchestration design, warehouse modeling, dbt transformations, BI-ready semantic assets, validation, monitoring, and local evidence generation. Managed cloud infrastructure, real vendor credentials, and enterprise BI administration are natural deployment extensions.
