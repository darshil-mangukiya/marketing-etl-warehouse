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
        event_bundle_sequence_id,
        batch_event_index,
        event_params,
        ecommerce,
        items,
        {{ ga4_event_param_string('page_location') }} as page_location,
        {{ ga4_event_param_string('ga_session_id') }} as ga_session_id,
        {{ ga4_event_param_string('currency') }} as event_currency,
        {{ ga4_event_param_string('transaction_id') }} as event_param_transaction_id
    from {{ source('ga4_live_export', 'events') }}
    where {{ ga4_live_suffix_predicate() }}
        and lower(event_name) in ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
),

item_rows as (
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
        item_offset,
        parse_date('%Y%m%d', event_date) as event_date,
        timestamp_micros(event_timestamp) as event_timestamp,
        event_name,
        lower(
            coalesce(
                net.host(page_location),
                regexp_extract(page_location, r'^(?:https?://)?([^/:?#]+)')
            )
        ) as hostname,
        case
            when user_pseudo_id is not null and safe_cast(ga_session_id as int64) is not null
                then to_hex(sha256(concat(user_pseudo_id, '|', ga_session_id)))
        end as session_key,
        case
            when event_name = 'purchase'
                then coalesce(ecommerce.transaction_id, event_param_transaction_id)
        end as transaction_id,
        upper(event_currency) as currency,
        item.item_id,
        item.item_name,
        item.item_category,
        cast(item.price as numeric) as price,
        coalesce(item.quantity, 1) as quantity,
        export_table_suffix,
        'live_ga4_export' as data_origin
    from source_events
    cross join unnest(items) as item with offset as item_offset
)

select
    concat(event_key, '|', cast(item_offset as string)) as item_event_key,
    event_key,
    session_key,
    event_date,
    event_timestamp,
    event_name,
    hostname,
    transaction_id,
    currency,
    item_id,
    item_name,
    item_category,
    price,
    quantity,
    export_table_suffix,
    data_origin
from item_rows
where hostname = lower('{{ var("ga4_live_hostname", "p2.darshilmangukiya.com") }}')

{% else %}

select null as item_event_key where false

{% endif %}
