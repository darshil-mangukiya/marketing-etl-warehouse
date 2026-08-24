{{ config(materialized='incremental', unique_key='lead_id', indexes=[{'columns': ['created_date']}, {'columns': ['campaign_key']}]) }}

select
    l.lead_id,
    l.created_date,
    cu.customer_key,
    ca.campaign_key,
    ch.channel_key,
    r.region_key,
    sr.sales_rep_key,
    l.qualification_stage,
    l.lead_score,
    l.attribution_id,
    l.cdc_operation,
    l.batch_id as load_batch_id,
    l.updated_at
from {{ ref('stg_crm_leads') }} l
left join {{ ref('dim_customer') }} cu
    on l.customer_id = cu.customer_id
   and cu.is_current
left join {{ ref('dim_campaign') }} ca
    on l.campaign_id = ca.campaign_id
   and ca.is_current
left join {{ ref('dim_channel') }} ch
    on l.normalized_channel = ch.channel_key
left join {{ ref('dim_region') }} r
    on l.region = r.region
   and r.country = 'UNKNOWN'
left join {{ ref('dim_sales_rep') }} sr
    on l.assigned_rep = sr.rep_id
{% if is_incremental() %}
where l.updated_at >= (select coalesce(max(target.updated_at), timestamp '1900-01-01') from {{ this }} as target)
{% endif %}
