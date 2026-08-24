select
    session_id,
    min(user_pseudo_id) as user_pseudo_id,
    min(event_timestamp) as session_started_at,
    max(event_timestamp) as session_ended_at,
    min(event_date) as session_date,
    min(source) as source,
    min(medium) as medium,
    min(campaign) as campaign,
    min(campaign_id) as campaign_id,
    min(landing_page) as landing_page,
    min(device_category) as device_category,
    min(region) as region,
    min(country) as country,
    count(*) as event_count,
    max(engagement_indicator) as engaged_session_indicator,
    max(conversion_indicator) as converted_session_indicator,
    sum(revenue) as session_revenue,
    max(updated_at) as updated_at
from {{ ref('stg_ga4_events') }}
group by session_id
