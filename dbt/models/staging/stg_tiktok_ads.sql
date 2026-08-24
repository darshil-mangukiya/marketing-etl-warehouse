select
    {{ surrogate_key(["source_system", "campaign_id", "event_date", "creative_id"]) }} as tiktok_ads_row_key,
    cast(event_date as date) as event_date,
    cast(campaign_id as {{ string_type() }}) as campaign_id,
    nullif(trim(campaign_name), '') as campaign_name,
    cast(creative_id as {{ string_type() }}) as creative_id,
    cast(country as {{ string_type() }}) as country,
    cast(video_views as bigint) as video_views,
    cast(clicks as bigint) as clicks,
    cast(coalesce(spend, 0) as {{ numeric_type(18, 2) }}) as spend,
    spend is null as null_spend_flag,
    cast(conversions as bigint) as conversions,
    cast(attribution_id as {{ string_type() }}) as attribution_id,
    cast(batch_id as {{ string_type() }}) as batch_id,
    cast(updated_at as timestamp) as updated_at,
    'paid_social' as normalized_channel,
    cast(source_system as {{ string_type() }}) as source_system
from {{ source('raw', 'tiktok_ads') }}
