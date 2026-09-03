create index if not exists idx_fact_campaign_event_date
    on warehouse.fact_campaign_performance (event_date);

create index if not exists idx_fact_campaign_campaign_key
    on warehouse.fact_campaign_performance (campaign_key);

create index if not exists idx_fact_sessions_event_date
    on warehouse.fact_sessions (event_date);

create index if not exists idx_fact_sessions_attribution
    on warehouse.fact_sessions (attribution_id);

create index if not exists idx_fact_leads_created_date
    on warehouse.fact_leads (created_date);

create index if not exists idx_fact_leads_campaign
    on warehouse.fact_leads (campaign_key);

create index if not exists idx_fact_conversions_conversion_date
    on warehouse.fact_conversions (conversion_date);

create index if not exists idx_fact_conversions_lead_id
    on warehouse.fact_conversions (lead_id);

create index if not exists idx_fact_attribution_touchpoint
    on warehouse.fact_attribution (touchpoint_date, conversion_date);

create index if not exists idx_dim_campaign_current
    on warehouse.dim_campaign (campaign_id, is_current);

comment on schema raw is 'Source-aligned landing schema populated from the local S3 raw zone.';
comment on schema staging is 'Typed, renamed, and lightly cleaned source views used by dbt staging models.';
comment on schema intermediate is 'Cross-source conformance and attribution preparation.';
comment on schema warehouse is 'Dimensional warehouse with conformed dimensions and facts.';
comment on schema mart is 'BI and semantic reporting marts.';

comment on table warehouse.dim_campaign is 'SCD Type 2 campaign dimension for canonical campaign and channel history.';
comment on table warehouse.dim_customer is 'SCD Type 2 customer acquisition dimension prepared for LTV analysis.';
comment on table warehouse.fact_campaign_performance is 'Daily paid-media performance grain by campaign, source, channel, and region.';
comment on table warehouse.fact_attribution is 'Attribution-ready bridge supporting first touch, last touch, and linear models.';

comment on column warehouse.fact_campaign_performance.event_date is 'Partition candidate in managed warehouses. In PostgreSQL, index by date and optionally monthly range partition at scale.';
comment on column warehouse.fact_sessions.event_date is 'Partition candidate for high-volume session facts.';
comment on column warehouse.fact_leads.cdc_operation is 'Simulated CDC operation code from CRM: I, U, or D.';
comment on column warehouse.fact_conversions.cdc_operation is 'Simulated CDC operation code from sales conversion source: I, U, or D.';
