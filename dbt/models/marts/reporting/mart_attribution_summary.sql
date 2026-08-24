select
    date_trunc('month', a.conversion_date)::date as reporting_month,
    a.attribution_model,
    ch.channel_name,
    ca.canonical_campaign_name,
    count(distinct a.conversion_id) as attributed_conversions,
    sum(a.attribution_weight) as weighted_conversions,
    sum(a.attributed_revenue) as attributed_revenue,
    avg(a.attribution_weight) as avg_touchpoint_weight
from {{ ref('fact_attribution') }} a
left join {{ ref('dim_channel') }} ch
    on a.channel_key = ch.channel_key
left join {{ ref('dim_campaign') }} ca
    on a.campaign_key = ca.campaign_key
group by 1, 2, 3, 4
