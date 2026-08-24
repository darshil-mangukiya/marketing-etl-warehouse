with targets as (
    select
        target_month,
        channel_name,
        sum(target_spend) as target_spend,
        sum(target_revenue) as target_revenue,
        sum(target_conversions) as target_conversions,
        {{ safe_divide('sum(target_revenue)', 'sum(target_spend)') }} as target_roas,
        {{ safe_divide('sum(target_spend)', 'sum(target_conversions)') }} as target_cac
    from {{ ref('mart_target_vs_actual') }}
    group by target_month, channel_name
),
evaluated as (
    select
        c.reporting_month,
        c.campaign_id,
        c.canonical_campaign_name as campaign_name,
        c.canonical_channel as channel,
        c.spend,
        c.attributed_revenue,
        c.attributed_roas as current_roas,
        {{ safe_divide('c.spend', 'c.platform_conversions') }} as current_cac,
        t.target_roas,
        t.target_cac,
        c.platform_conversions,
        case when c.campaign_id is null or c.campaign_id = '' then 'HOLD' else 'PASS' end as data_quality_status
    from {{ ref('mart_campaign_performance') }} c
    left join targets t
        on c.reporting_month = t.target_month
       and lower(c.canonical_channel) = lower(t.channel_name)
)
select
    reporting_month,
    campaign_id,
    campaign_name,
    channel,
    spend,
    attributed_revenue,
    current_roas,
    current_cac,
    target_roas,
    target_cac,
    case
        when data_quality_status <> 'PASS' then 'DATA_QUALITY_HOLD'
        when target_roas is null then 'TARGET_REVIEW_REQUIRED'
        when current_roas >= target_roas * {{ var('campaign_scale_roas_multiplier') }} then 'ABOVE_TARGET'
        when current_roas < target_roas * {{ var('campaign_reduce_roas_multiplier') }} then 'BELOW_TARGET'
        else 'NEAR_TARGET'
    end as performance_status,
    case
        when data_quality_status <> 'PASS' then 'P0'
        when spend >= {{ var('campaign_min_spend_for_action') }} and current_roas < target_roas * {{ var('campaign_reduce_roas_multiplier') }} then 'P1'
        when current_roas >= target_roas * {{ var('campaign_scale_roas_multiplier') }} then 'P2'
        else 'P3'
    end as action_priority,
    case
        when data_quality_status <> 'PASS' then 'DATA QUALITY HOLD'
        when target_roas is null then 'REVIEW TARGET'
        when current_roas >= target_roas * {{ var('campaign_scale_roas_multiplier') }} then 'SCALE'
        when current_roas < target_roas * {{ var('campaign_reduce_roas_multiplier') }} and platform_conversions = 0 then 'FIX FUNNEL'
        when current_roas < target_roas * {{ var('campaign_reduce_roas_multiplier') }} then 'REDUCE'
        else 'MONITOR'
    end as recommended_action,
    case
        when data_quality_status <> 'PASS' then 'Campaign identifier is missing; withhold budget action until mapping is corrected.'
        when target_roas is null then 'No governed target matched this channel and month.'
        when current_roas >= target_roas * {{ var('campaign_scale_roas_multiplier') }} then 'ROAS materially exceeds the governed channel target.'
        when platform_conversions = 0 then 'Spend is present without platform conversions.'
        when current_roas < target_roas * {{ var('campaign_reduce_roas_multiplier') }} then 'ROAS materially trails the governed channel target.'
        else 'Performance is close to target and should be monitored.'
    end as action_reason,
    'ROAS' as supporting_metric,
    data_quality_status,
    case when platform_conversions = 0 and data_quality_status = 'PASS' then 'conversion_rate' else 'roas' end as metric_to_monitor,
    current_timestamp as generated_at
from evaluated
