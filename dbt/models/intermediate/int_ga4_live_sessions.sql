{{
    config(
        enabled=target.type == 'bigquery',
        materialized='view',
        tags=['ga4_live', 'intermediate']
    )
}}

{% if target.type == 'bigquery' %}

select
    to_hex(sha256(concat(user_pseudo_id, '|', cast(ga_session_id as string)))) as session_key,
    to_hex(sha256(user_pseudo_id)) as user_key,
    min(event_date) as session_date,
    min(event_timestamp) as session_started_at,
    max(event_timestamp) as session_ended_at,
    timestamp_diff(max(event_timestamp), min(event_timestamp), second) as session_duration_seconds,
    count(*) as event_count,
    countif(event_name = 'page_view') as page_view_count,
    countif(event_name = 'view_item') as view_item_count,
    countif(event_name = 'add_to_cart') as add_to_cart_count,
    countif(event_name = 'begin_checkout') as begin_checkout_count,
    countif(event_name = 'purchase') as purchase_count,
    min(case when event_name = 'view_item' then event_timestamp end) as first_view_item_at,
    min(case when event_name = 'add_to_cart' then event_timestamp end) as first_add_to_cart_at,
    min(case when event_name = 'begin_checkout' then event_timestamp end) as first_begin_checkout_at,
    min(case when event_name = 'purchase' then event_timestamp end) as first_purchase_at,
    max(
        case
            when session_engaged in ('1', 'true', 'yes') or event_name = 'user_engagement' then 1
            else 0
        end
    ) as engaged_session_indicator,
    sum(coalesce(engagement_time_msec, 0)) as engagement_time_msec,
    sum(case when event_name = 'purchase' then coalesce(value, 0) else 0 end) as purchase_value,
    count(distinct case when event_name = 'purchase' then transaction_id end) as purchase_transaction_count,
    max(case when event_name = 'purchase' then 1 else 0 end) as converted_session_indicator,
    array_agg(source ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as source,
    array_agg(medium ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as medium,
    array_agg(campaign ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as campaign,
    array_agg(page_location ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as landing_page,
    array_agg(device_category ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as device_category,
    array_agg(country ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as country,
    array_agg(region ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as region,
    array_agg(city ignore nulls order by event_timestamp limit 1)[safe_offset(0)] as city,
    '{{ var("ga4_live_hostname", "p2.darshilmangukiya.com") }}' as hostname,
    'live_ga4_export' as data_origin
from {{ ref('stg_ga4_live_events') }}
where user_pseudo_id is not null
    and ga_session_id is not null
group by user_pseudo_id, ga_session_id

{% else %}

select null as session_key where false

{% endif %}
