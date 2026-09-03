select
    {{ month_start('f.event_date') }} as reporting_month,
    ca.campaign_id,
    ca.canonical_campaign_name,
    ca.canonical_channel,
    ca.owner_team,
    sum(f.spend) as spend,
    sum(f.impressions) as impressions,
    sum(f.clicks) as clicks,
    sum(f.conversions) as platform_conversions,
    sum(f.revenue) as attributed_revenue,
    {{ safe_divide('sum(f.clicks)', 'sum(f.impressions)') }} as ctr,
    {{ safe_divide('sum(f.spend)', 'sum(f.clicks)') }} as cpc,
    {{ safe_divide('sum(f.revenue)', 'sum(f.spend)') }} as attributed_roas,
    case
        when sum(f.spend) > 10000 and coalesce(sum(f.revenue) / nullif(sum(f.spend), 0), 0) < 1 then true
        else false
    end as waste_budget_flag
from {{ ref('fact_campaign_performance') }} f
left join {{ ref('dim_campaign') }} ca
    on f.campaign_key = ca.campaign_key
group by 1, 2, 3, 4, 5
