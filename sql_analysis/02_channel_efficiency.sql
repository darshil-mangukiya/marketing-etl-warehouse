-- Business question: Which channels convert spend into revenue and margin most efficiently?
-- Source: data/exports/demo_mart_channel_performance.csv (synthetic BI export, local review).
-- Dialect: DuckDB. Reads the generated BI export CSV for reproducible local review.

with channel as (
    select
        normalized_channel,
        channel_name,
        cast(spend as double)                  as spend,
        cast(clicks as bigint)                 as clicks,
        cast(impressions as bigint)            as impressions,
        cast(leads as bigint)                  as leads,
        cast(closed_won_conversions as bigint) as conversions,
        cast(booked_revenue as double)         as booked_revenue,
        cast(gross_margin as double)           as gross_margin
    from read_csv_auto('data/exports/demo_mart_channel_performance.csv', header=true)
),
rolled_up as (
    -- collapse any month-level rows to one row per channel before ranking
    select
        normalized_channel,
        max(channel_name)   as channel_name,
        sum(spend)          as spend,
        sum(clicks)         as clicks,
        sum(impressions)    as impressions,
        sum(leads)          as leads,
        sum(conversions)    as conversions,
        sum(booked_revenue) as booked_revenue,
        sum(gross_margin)   as gross_margin
    from channel
    group by normalized_channel
),
scored as (
    select
        normalized_channel,
        channel_name,
        spend,
        conversions,
        booked_revenue,
        gross_margin,
        round(booked_revenue / nullif(spend, 0), 2)             as roas,
        round(gross_margin / nullif(spend, 0), 2)               as margin_on_spend,
        round(spend / nullif(conversions, 0), 2)                as cost_per_conversion,
        round(clicks * 1.0 / nullif(impressions, 0), 4)         as ctr,
        round(spend / nullif(clicks, 0), 2)                     as cost_per_click,
        round(100.0 * spend / nullif(sum(spend) over (), 0), 1) as spend_share_pct
    from rolled_up
)
select
    normalized_channel,
    channel_name,
    spend,
    spend_share_pct,
    conversions,
    booked_revenue,
    roas,
    margin_on_spend,
    cost_per_conversion,
    ctr,
    cost_per_click,
    rank() over (order by roas desc, margin_on_spend desc) as efficiency_rank,
    case
        when roas >= 4 then 'scale'
        when roas >= 2 then 'maintain'
        else 'review'
    end as budget_action
from scored
order by roas desc, booked_revenue desc;
