select
    cast(lead_id as text) as lead_id,
    cast(customer_id as text) as customer_id,
    cast(created_at as date) as created_date,
    {{ normalize_channel("lead_source") }} as normalized_channel,
    cast(lead_source as text) as lead_source,
    cast(campaign_id as text) as campaign_id,
    cast(qualification_stage as text) as qualification_stage,
    cast(lead_score as numeric(6, 2)) as lead_score,
    cast(assigned_rep as text) as assigned_rep,
    cast(region as text) as region,
    cast(attribution_id as text) as attribution_id,
    cast(cdc_operation as text) as cdc_operation,
    cast(batch_id as text) as batch_id,
    cast(updated_at as timestamp) as updated_at,
    cast(source_system as text) as source_system
from {{ source('raw', 'crm_leads') }}
where coalesce(cdc_operation, 'I') <> 'D'
