-- Business question: Which campaigns drive the strongest and weakest return, and where is spend wasted?
-- Source: data/exports/demo_mart_campaign_performance.csv (synthetic BI export, local review).
-- Dialect: DuckDB. Reads the generated BI export CSV for reproducible local review.

with campaigns as (
    select
        campaign_id,
        campaign_name,
        normalized_channel,
        cast(spend as double)              as spend,
        cast(impressions as bigint)        as impressions,
        cast(clicks as bigint)             as clicks,
        cast(conversions as bigint)        as conversions,
        cast(attributed_revenue as double) as attributed_revenue,
        cast(attributed_roas as double)    as attributed_roas,
        waste_budget_flag
    from read_csv_auto('data/exports/demo_mart_campaign_performance.csv', header=true)
),
scored as (
    select
        campaign_id,
        campaign_name,
        normalized_channel,
        spend,
        conversions,
        attributed_revenue,
        attributed_roas,
        waste_budget_flag,
        round(clicks * 1.0 / nullif(impressions, 0), 4) as ctr,
        round(spend / nullif(clicks, 0), 2)             as cost_per_click,
        round(spend / nullif(conversions, 0), 2)        as cost_per_conversion,
        round(attributed_revenue - spend, 2)            as net_contribution,
        case
            when attributed_roas >= 4 then 'scale'
            when attributed_roas >= 2 then 'maintain'
            when spend > 0 then 'review'
            else 'no_spend'
        end as roi_tier
    from campaigns
)
select
    campaign_id,
    campaign_name,
    normalized_channel,
    spend,
    conversions,
    attributed_revenue,
    attributed_roas,
    net_contribution,
    ctr,
    cost_per_click,
    cost_per_conversion,
    roi_tier,
    waste_budget_flag,
    rank() over (order by attributed_roas desc, attributed_revenue desc) as roas_rank
from scored
order by attributed_roas desc, attributed_revenue desc;
