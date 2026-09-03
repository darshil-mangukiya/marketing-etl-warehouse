{{ config(materialized='incremental', unique_key='session_id', indexes=[{'columns': ['event_date']}, {'columns': ['attribution_id']}]) }}

select
    s.session_id,
    s.event_date,
    c.campaign_key,
    ch.channel_key,
    r.region_key,
    d.device_key,
    s.visitor_id,
    s.page_views,
    s.session_duration_seconds,
    s.bounce_flag,
    s.attribution_id,
    s.batch_id as load_batch_id,
    s.updated_at
from {{ ref('stg_website_analytics') }} s
left join {{ ref('dim_campaign') }} c
    on s.campaign_id = c.campaign_id
   and c.is_current
left join {{ ref('dim_channel') }} ch
    on s.normalized_channel = ch.channel_key
left join {{ ref('dim_region') }} r
    on s.country = r.country
left join {{ ref('dim_device') }} d
    on s.device = d.device_key
{% if is_incremental() %}
where s.updated_at >= (select coalesce(max(target.updated_at), timestamp '1900-01-01') from {{ this }} as target)
{% endif %}
