with model_revenue as (
    select
        date_trunc('month', a.conversion_date)::date as reporting_month,
        ch.channel_name,
        ca.canonical_campaign_name,
        a.attribution_model,
        sum(a.attributed_revenue) as attributed_revenue,
        sum(a.attribution_weight) as weighted_conversions
    from {{ ref('fact_attribution') }} a
    left join {{ ref('dim_channel') }} ch
        on a.channel_key = ch.channel_key
    left join {{ ref('dim_campaign') }} ca
        on a.campaign_key = ca.campaign_key
    group by 1, 2, 3, 4
),
pivoted as (
    select
        reporting_month,
        channel_name,
        canonical_campaign_name,
        sum(attributed_revenue) filter (where attribution_model = 'first_touch') as first_touch_revenue,
        sum(attributed_revenue) filter (where attribution_model = 'last_touch') as last_touch_revenue,
        sum(attributed_revenue) filter (where attribution_model = 'linear') as linear_revenue,
        sum(attributed_revenue) filter (where attribution_model = 'u_shaped') as u_shaped_revenue,
        sum(attributed_revenue) filter (where attribution_model = 'time_decay') as time_decay_revenue,
        sum(attributed_revenue) filter (where attribution_model = 'position_based') as position_based_revenue,
        sum(weighted_conversions) filter (where attribution_model = 'linear') as linear_weighted_conversions
    from model_revenue
    group by 1, 2, 3
)
select
    *,
    coalesce(last_touch_revenue, 0) - coalesce(first_touch_revenue, 0) as last_vs_first_revenue_delta,
    coalesce(time_decay_revenue, 0) - coalesce(linear_revenue, 0) as time_decay_vs_linear_revenue_delta,
    coalesce(u_shaped_revenue, 0) - coalesce(linear_revenue, 0) as u_shaped_vs_linear_revenue_delta
from pivoted
