# Power BI Service Deployment Readiness

## Implemented

- Existing PBIX preserved unchanged, plus source-controlled PBIP/TMDL, DAX, relationships, RLS mockup, refresh guidance and CSV handoff.
- BigQuery-ready dataset design and new GA4 funnel, variance-driver, campaign-action and source-health outputs.
- UAT cases for reconciliation, filters, refresh and RLS.

## Requires manual Power BI Service configuration

1. Create/select a workspace with the intended license/capacity.
2. Open the preserved PBIX in Power BI Desktop, point Power Query to BigQuery marts (or keep local CSV for demo), validate relationships/measures, and publish.
3. In the Service semantic-model settings, configure Google/organizational credentials and privacy level, then test connection.
4. Configure scheduled refresh only after a successful manual refresh. BigQuery is cloud-to-cloud, so an on-premises gateway is generally unnecessary; a gateway is required if any retained source is local/on-premises.
5. Define RLS roles in Desktop/TMDL, publish, map users/groups in Security, and use “Test as role.”
6. Execute `docs/uat_test_cases.csv`, capture refresh history, lineage, security and report screenshots, and record the deployment commit.

Record Power BI Service deployment, scheduled refresh, and RLS results after completing the interface-based checks.
