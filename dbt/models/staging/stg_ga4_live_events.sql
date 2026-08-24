{{
    config(
        enabled=target.type == 'bigquery',
        materialized='view',
        tags=['ga4_live', 'staging']
    )
}}

{% if target.type == 'bigquery' %}

with source_events as (
    select
        _table_suffix as export_table_suffix,
        event_date,
        event_timestamp,
        lower(event_name) as event_name,
        user_pseudo_id,
        stream_id,
        platform,
        event_bundle_sequence_id,
        batch_event_index,
        event_params,
        device,
        geo,
        traffic_source,
        collected_traffic_source,
        session_traffic_source_last_click,
        ecommerce,
        {{ ga4_event_param_string('page_location') }} as page_location,
        {{ ga4_event_param_string('page_title') }} as page_title,
        {{ ga4_event_param_string('ga_session_id') }} as ga_session_id,
        {{ ga4_event_param_string('ga_session_number') }} as ga_session_number,
        lower({{ ga4_event_param_string('session_engaged') }}) as session_engaged,
        cast({{ ga4_event_param_numeric('engagement_time_msec') }} as int64) as engagement_time_msec,
        upper({{ ga4_event_param_string('currency') }}) as currency,
        {{ ga4_event_param_numeric('value') }} as event_value,
        {{ ga4_event_param_string('transaction_id') }} as event_param_transaction_id
    from {{ source('ga4_live_export', 'events') }}
    where {{ ga4_live_suffix_predicate() }}
),

normalized as (
    select
        to_hex(
            sha256(
                concat(
                    coalesce(user_pseudo_id, 'anonymous'), '|',
                    cast(event_timestamp as string), '|',
                    coalesce(event_name, 'unknown'), '|',
                    coalesce(cast(event_bundle_sequence_id as string), ''), '|',
                    coalesce(cast(batch_event_index as string), ''), '|',
                    export_table_suffix
                )
            )
        ) as event_key,
        parse_date('%Y%m%d', event_date) as event_date,
        timestamp_micros(event_timestamp) as event_timestamp,
        event_name,
        user_pseudo_id,
        safe_cast(ga_session_id as int64) as ga_session_id,
        safe_cast(ga_session_number as int64) as ga_session_number,
        stream_id,
        platform,
        page_location,
        page_title,
        lower(
            coalesce(
                net.host(page_location),
                regexp_extract(page_location, r'^(?:https?://)?([^/:?#]+)')
            )
        ) as hostname,
        session_engaged,
        engagement_time_msec,
        currency,
        event_value as value,
        case
            when event_name = 'purchase'
                then coalesce(ecommerce.transaction_id, event_param_transaction_id)
        end as transaction_id,
        coalesce(
            session_traffic_source_last_click.cross_channel_campaign.source,
            collected_traffic_source.manual_source,
            traffic_source.source,
            '(direct)'
        ) as source,
        coalesce(
            session_traffic_source_last_click.cross_channel_campaign.medium,
            collected_traffic_source.manual_medium,
            traffic_source.medium,
            '(none)'
        ) as medium,
        coalesce(
            session_traffic_source_last_click.cross_channel_campaign.campaign_name,
            collected_traffic_source.manual_campaign_name,
            traffic_source.name,
            '(not set)'
        ) as campaign,
        lower(device.category) as device_category,
        coalesce(device.web_info.browser, device.browser) as browser,
        device.operating_system as operating_system,
        geo.country as country,
        geo.region as region,
        geo.city as city,
        export_table_suffix,
        'live_ga4_export' as data_origin
    from source_events
)

select
    event_key,
    event_date,
    event_timestamp,
    event_name,
    user_pseudo_id,
    ga_session_id,
    ga_session_number,
    stream_id,
    platform,
    page_location,
    page_title,
    hostname,
    session_engaged,
    engagement_time_msec,
    currency,
    value,
    transaction_id,
    source,
    medium,
    campaign,
    device_category,
    browser,
    operating_system,
    country,
    region,
    city,
    export_table_suffix,
    data_origin
from normalized
where hostname = lower('{{ var("ga4_live_hostname", "p2.darshilmangukiya.com") }}')

{% else %}

select null as event_key where false

{% endif %}
