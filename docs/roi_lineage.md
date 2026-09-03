# Campaign ROI Lineage

Generated source profiles make the ROI lineage reproducible without customer or advertising-account records. Business-impact examples are analytical scenarios rather than measured operating outcomes.

Campaign ROI is the project headline metric. The lineage is:

1. Paid media source rows provide spend, impressions, clicks, conversions, campaign identifiers, channels, and update timestamps.
2. Staging models normalize campaign/channel/date fields and clean source-specific types.
3. Intermediate models unify campaign spend and build campaign daily performance.
4. Lead and conversion sources provide funnel and revenue context.
5. Attribution models assign revenue to touchpoints/campaigns.
6. Reporting marts calculate attributed revenue, attributed ROAS, and campaign ROI using governed formulas.
7. Streamlit, SQL analysis, Python analysis, and Power BI DAX reference the same KPI catalog definitions.

Formula:

`campaign_roi = (attributed_revenue - spend) / spend`

`attributed_roas = attributed_revenue / spend`
