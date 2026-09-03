select
    cast(target_month || '-01' as date) as target_month,
    cast(region as text) as region,
    cast(channel as text) as normalized_channel,
    cast(target_spend as numeric(18, 2)) as target_spend,
    cast(target_revenue as numeric(18, 2)) as target_revenue,
    cast(target_leads as integer) as target_leads,
    cast(target_conversions as integer) as target_conversions,
    cast(budget_owner as text) as budget_owner,
    cast(batch_id as text) as batch_id
from {{ source('raw', 'marketing_targets') }}
