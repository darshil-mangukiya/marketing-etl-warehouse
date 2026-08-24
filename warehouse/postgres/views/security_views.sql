create schema if not exists security;

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'marketing_bi_reader') then
        create role marketing_bi_reader;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'marketing_analytics_engineer') then
        create role marketing_analytics_engineer;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'marketing_data_engineer') then
        create role marketing_data_engineer;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'marketing_finance_reader') then
        create role marketing_finance_reader;
    end if;
end
$$;

grant usage on schema mart to marketing_bi_reader;
grant usage on schema warehouse to marketing_analytics_engineer;
grant usage on schema raw to marketing_data_engineer;
grant usage on schema security to marketing_bi_reader, marketing_analytics_engineer, marketing_finance_reader;

create or replace view security.masked_dim_customer as
select
    customer_key,
    encode(sha256(customer_id::bytea), 'hex') as customer_id_hash,
    first_lead_date,
    first_conversion_date,
    acquisition_channel,
    customer_segment,
    valid_from,
    valid_to,
    is_current
from warehouse.dim_customer;

create or replace view security.masked_fact_leads as
select
    encode(sha256(lead_id::bytea), 'hex') as lead_id_hash,
    created_date,
    customer_key,
    campaign_key,
    channel_key,
    region_key,
    sales_rep_key,
    qualification_stage,
    lead_score,
    case when attribution_id is null then null else encode(sha256(attribution_id::bytea), 'hex') end as attribution_id_hash,
    cdc_operation,
    load_batch_id,
    loaded_at
from warehouse.fact_leads;

create or replace view security.masked_fact_conversions as
select
    encode(sha256(conversion_id::bytea), 'hex') as conversion_id_hash,
    conversion_date,
    case when lead_id is null then null else encode(sha256(lead_id::bytea), 'hex') end as lead_id_hash,
    customer_key,
    campaign_key,
    product_key,
    deal_value,
    gross_margin,
    case when attribution_id is null then null else encode(sha256(attribution_id::bytea), 'hex') end as attribution_id_hash,
    cdc_operation,
    load_batch_id,
    loaded_at
from warehouse.fact_conversions;

create or replace view security.executive_channel_performance as
select
    reporting_month,
    channel_name,
    normalized_channel,
    spend,
    booked_revenue,
    gross_margin,
    leads,
    qualified_leads,
    closed_won_conversions,
    ctr,
    cpc,
    cac,
    roas,
    mer
from mart.mart_channel_performance;

grant select on security.masked_dim_customer to marketing_analytics_engineer;
grant select on security.masked_fact_leads to marketing_analytics_engineer;
grant select on security.masked_fact_conversions to marketing_analytics_engineer, marketing_finance_reader;
grant select on security.executive_channel_performance to marketing_bi_reader, marketing_finance_reader;
