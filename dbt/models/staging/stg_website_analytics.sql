select
    cast(session_id as {{ string_type() }}) as session_id,
    cast(event_date as date) as event_date,
    cast(visitor_id as {{ string_type() }}) as visitor_id,
    cast(utm_campaign_id as {{ string_type() }}) as campaign_id,
    nullif(trim(utm_campaign), '') as campaign_name,
    {{ normalize_channel("traffic_source") }} as normalized_channel,
    cast(traffic_source as {{ string_type() }}) as traffic_source,
    case when lower(device) in ('desktop', 'mobile', 'tablet', 'unknown') then lower(device) else 'unknown' end as device,
    cast(country as {{ string_type() }}) as country,
    cast(page_views as integer) as page_views,
    cast(session_duration_seconds as integer) as session_duration_seconds,
    case
        when lower(cast(bounce_flag as {{ string_type() }})) in ('true', 't', '1', 'yes') then true
        when lower(cast(bounce_flag as {{ string_type() }})) in ('false', 'f', '0', 'no') then false
        else null
    end as bounce_flag,
    cast(attribution_id as {{ string_type() }}) as attribution_id,
    cast(batch_id as {{ string_type() }}) as batch_id,
    cast(updated_at as timestamp) as updated_at,
    cast(source_system as {{ string_type() }}) as source_system
from {{ source('raw', 'website_analytics') }}
