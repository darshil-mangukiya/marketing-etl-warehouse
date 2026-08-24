with models as (
    select 'first_touch' as attribution_model, first_touch_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
    union all
    select 'last_touch' as attribution_model, last_touch_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
    union all
    select 'linear' as attribution_model, linear_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
    union all
    select 'u_shaped' as attribution_model, u_shaped_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
    union all
    select 'time_decay' as attribution_model, time_decay_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
    union all
    select 'position_based' as attribution_model, position_based_weight as attribution_weight, * from {{ ref('int_attribution_touchpoints') }}
)
select
    {{ surrogate_key(["m.conversion_id", "m.campaign_id", "m.touchpoint_date", "m.attribution_model", "coalesce(m.session_id, '')"]) }} as fact_attribution_key,
    m.attribution_id,
    m.conversion_id,
    cu.customer_key,
    ca.campaign_key,
    ch.channel_key,
    m.touchpoint_date,
    m.conversion_date,
    m.attribution_model,
    m.attribution_weight,
    m.deal_value * m.attribution_weight as attributed_revenue
from models m
left join {{ ref('dim_customer') }} cu
    on m.customer_id = cu.customer_id
   and cu.is_current
left join {{ ref('dim_campaign') }} ca
    on m.campaign_id = ca.campaign_id
   and ca.is_current
left join {{ ref('dim_channel') }} ch
    on m.normalized_channel = ch.channel_key
