with campaign as (
    select
        date_trunc('month', f.event_date)::date as reporting_month,
        ch.channel_key,
        ch.channel_name,
        ch.channel_group,
        sum(f.spend) as spend,
        sum(f.impressions) as impressions,
        sum(f.clicks) as clicks,
        sum(f.conversions) as platform_conversions,
        sum(f.revenue) as attributed_revenue
    from {{ ref('fact_campaign_performance') }} f
    left join {{ ref('dim_channel') }} ch
        on f.channel_key = ch.channel_key
    group by 1, 2, 3, 4
),
leads as (
    select
        date_trunc('month', l.created_date)::date as reporting_month,
        l.channel_key,
        count(*) as leads,
        count(*) filter (where qualification_stage in ('marketing_qualified', 'sales_accepted', 'sales_qualified')) as qualified_leads
    from {{ ref('fact_leads') }} l
    group by 1, 2
),
conversions as (
    select
        date_trunc('month', c.conversion_date)::date as reporting_month,
        ca.canonical_channel as channel_key,
        count(*) as closed_won_conversions,
        sum(c.deal_value) as booked_revenue,
        sum(c.gross_margin) as gross_margin
    from {{ ref('fact_conversions') }} c
    left join {{ ref('dim_campaign') }} ca
        on c.campaign_key = ca.campaign_key
    group by 1, 2
)
select
    coalesce(c.reporting_month, l.reporting_month, cn.reporting_month) as reporting_month,
    coalesce(c.channel_key, l.channel_key, cn.channel_key) as channel_key,
    max(c.channel_name) as channel_name,
    max(c.channel_group) as channel_group,
    coalesce(sum(c.spend), 0) as spend,
    coalesce(sum(c.impressions), 0) as impressions,
    coalesce(sum(c.clicks), 0) as clicks,
    coalesce(sum(l.leads), 0) as leads,
    coalesce(sum(l.qualified_leads), 0) as qualified_leads,
    coalesce(sum(c.platform_conversions), 0) as platform_conversions,
    coalesce(sum(cn.closed_won_conversions), 0) as closed_won_conversions,
    coalesce(sum(c.attributed_revenue), 0) as attributed_revenue,
    coalesce(sum(cn.booked_revenue), 0) as booked_revenue,
    coalesce(sum(cn.gross_margin), 0) as gross_margin,
    coalesce(sum(c.clicks), 0)::numeric / nullif(sum(c.impressions), 0) as ctr,
    coalesce(sum(c.spend), 0) / nullif(sum(c.clicks), 0) as cpc,
    coalesce(sum(c.spend), 0) / nullif(sum(l.leads), 0) as cost_per_lead,
    coalesce(sum(c.spend), 0) / nullif(sum(cn.closed_won_conversions), 0) as cac,
    coalesce(sum(cn.booked_revenue), 0) / nullif(sum(c.spend), 0) as roas,
    coalesce(sum(cn.gross_margin), 0) / nullif(sum(c.spend), 0) as mer
from campaign c
full outer join leads l
    on c.reporting_month = l.reporting_month
   and c.channel_key = l.channel_key
full outer join conversions cn
    on coalesce(c.reporting_month, l.reporting_month) = cn.reporting_month
   and coalesce(c.channel_key, l.channel_key) = cn.channel_key
group by 1, 2
