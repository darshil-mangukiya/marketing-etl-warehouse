select
    {{ surrogate_key(["t.target_month", "t.region", "t.normalized_channel"]) }} as fact_target_key,
    t.target_month,
    r.region_key,
    ch.channel_key,
    t.target_spend,
    t.target_revenue,
    t.target_leads,
    t.target_conversions,
    t.budget_owner,
    t.batch_id as load_batch_id
from {{ ref('stg_marketing_targets') }} t
left join {{ ref('dim_region') }} r
    on t.region = r.region
   and r.country = 'UNKNOWN'
left join {{ ref('dim_channel') }} ch
    on t.normalized_channel = ch.channel_key
