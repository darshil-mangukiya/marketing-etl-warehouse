with actuals as (
    select
        date_trunc('month', event_date)::date as target_month,
        region_key,
        channel_key,
        sum(spend) as actual_spend,
        sum(revenue) as actual_revenue,
        sum(conversions) as actual_platform_conversions
    from {{ ref('fact_campaign_performance') }}
    group by 1, 2, 3
),
lead_actuals as (
    select
        date_trunc('month', created_date)::date as target_month,
        region_key,
        channel_key,
        count(*) as actual_leads
    from {{ ref('fact_leads') }}
    group by 1, 2, 3
)
select
    t.target_month,
    r.region,
    ch.channel_name,
    t.target_spend,
    coalesce(a.actual_spend, 0) as actual_spend,
    coalesce(a.actual_spend, 0) - t.target_spend as spend_variance,
    coalesce(a.actual_spend, 0) / nullif(t.target_spend, 0) as spend_attainment,
    t.target_revenue,
    coalesce(a.actual_revenue, 0) as actual_revenue,
    coalesce(a.actual_revenue, 0) - t.target_revenue as revenue_variance,
    coalesce(a.actual_revenue, 0) / nullif(t.target_revenue, 0) as revenue_attainment,
    t.target_leads,
    coalesce(l.actual_leads, 0) as actual_leads,
    coalesce(l.actual_leads, 0)::numeric / nullif(t.target_leads, 0) as lead_attainment,
    t.target_conversions,
    coalesce(a.actual_platform_conversions, 0) as actual_platform_conversions,
    coalesce(a.actual_platform_conversions, 0)::numeric / nullif(t.target_conversions, 0) as conversion_attainment,
    t.budget_owner
from {{ ref('fact_targets') }} t
left join actuals a
    on t.target_month = a.target_month
   and t.region_key = a.region_key
   and t.channel_key = a.channel_key
left join lead_actuals l
    on t.target_month = l.target_month
   and t.region_key = l.region_key
   and t.channel_key = l.channel_key
left join {{ ref('dim_region') }} r
    on t.region_key = r.region_key
left join {{ ref('dim_channel') }} ch
    on t.channel_key = ch.channel_key
