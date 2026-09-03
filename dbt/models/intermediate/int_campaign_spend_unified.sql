with paid_media as (
    select
        event_date,
        campaign_id,
        campaign_name,
        normalized_channel,
        source_system,
        region,
        cast(null as {{ string_type() }}) as country,
        impressions as exposure_count,
        clicks,
        spend,
        conversions,
        attribution_id,
        batch_id,
        updated_at
    from {{ ref('stg_google_ads') }}

    union all

    select
        event_date,
        campaign_id,
        campaign_name,
        normalized_channel,
        source_system,
        cast(null as {{ string_type() }}) as region,
        country,
        impressions as exposure_count,
        clicks,
        spend,
        conversions,
        attribution_id,
        batch_id,
        updated_at
    from {{ ref('stg_facebook_ads') }}

    union all

    select
        event_date,
        campaign_id,
        campaign_name,
        normalized_channel,
        source_system,
        cast(null as {{ string_type() }}) as region,
        country,
        video_views as exposure_count,
        clicks,
        spend,
        conversions,
        attribution_id,
        batch_id,
        updated_at
    from {{ ref('stg_tiktok_ads') }}
),
with_region as (
    select
        p.*,
        coalesce(p.region, r.region, 'UNKNOWN') as reporting_region,
        coalesce(p.country, r.country, 'UNKNOWN') as reporting_country
    from paid_media p
    left join {{ ref('stg_region_mapping') }} r
        on p.country = r.country
)
select
    {{ surrogate_key(["source_system", "campaign_id", "event_date", "coalesce(attribution_id, '')"]) }} as campaign_spend_row_key,
    event_date,
    campaign_id,
    campaign_name,
    normalized_channel,
    source_system,
    region,
    country,
    greatest(coalesce(exposure_count, 0), coalesce(clicks, 0)) as exposure_count,
    coalesce(clicks, 0) as clicks,
    coalesce(spend, 0) as spend,
    coalesce(conversions, 0) as conversions,
    attribution_id,
    batch_id,
    updated_at,
    reporting_region,
    reporting_country
from with_region
