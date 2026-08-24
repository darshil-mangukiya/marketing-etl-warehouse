{{ config(
    materialized='incremental',
    unique_key='fact_campaign_performance_key',
    indexes=[
      {'columns': ['event_date']},
      {'columns': ['campaign_key']},
      {'columns': ['channel_key']}
    ]
) }}

with campaign_daily as (
    select *
    from {{ ref('int_campaign_daily') }}
    {% if is_incremental() %}
    where updated_at >= (select coalesce(max(target.updated_at), timestamp '1900-01-01') from {{ this }} as target)
    {% endif %}
)
select
    {{ surrogate_key(["d.event_date", "d.campaign_id", "d.normalized_channel", "d.source_system", "d.reporting_region"]) }} as fact_campaign_performance_key,
    d.event_date,
    c.campaign_key,
    ch.channel_key,
    ss.source_system_key,
    r.region_key,
    d.impressions_or_views as impressions,
    d.clicks,
    d.spend,
    d.platform_conversions as conversions,
    coalesce(ar.attributed_revenue, 0) as revenue,
    d.source_row_count,
    d.batch_id as load_batch_id,
    d.updated_at
from campaign_daily d
left join {{ ref('dim_campaign') }} c
    on d.campaign_id = c.campaign_id
   and c.is_current
left join {{ ref('dim_channel') }} ch
    on d.normalized_channel = ch.channel_key
left join {{ ref('dim_source_system') }} ss
    on d.source_system = ss.source_system_key
left join {{ ref('dim_region') }} r
    on d.reporting_region = r.region
   and r.country = 'UNKNOWN'
left join (
    select campaign_id, normalized_channel, touchpoint_date, sum(deal_value * linear_weight) as attributed_revenue
    from {{ ref('int_attribution_touchpoints') }}
    group by 1, 2, 3
) ar
    on d.campaign_id = ar.campaign_id
   and d.normalized_channel = ar.normalized_channel
   and d.event_date = ar.touchpoint_date
