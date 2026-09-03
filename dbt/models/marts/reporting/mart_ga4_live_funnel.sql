{{
    config(
        enabled=target.type == 'bigquery',
        materialized='table',
        tags=['ga4_live', 'reporting', 'bi']
    )
}}

{% if target.type == 'bigquery' %}

select
    session_date,
    source,
    medium,
    campaign,
    count(*) as sessions,
    count(distinct user_key) as users,
    countif(engaged_session_indicator = 1) as engaged_sessions,
    countif(view_item_count > 0) as view_item_sessions,
    count(distinct case when view_item_count > 0 then user_key end) as view_item_users,
    countif(add_to_cart_count > 0) as add_to_cart_sessions,
    count(distinct case when add_to_cart_count > 0 then user_key end) as add_to_cart_users,
    countif(begin_checkout_count > 0) as begin_checkout_sessions,
    count(distinct case when begin_checkout_count > 0 then user_key end) as begin_checkout_users,
    countif(purchase_count > 0) as purchase_sessions,
    count(distinct case when purchase_count > 0 then user_key end) as purchase_users,
    {{ safe_divide('countif(add_to_cart_count > 0)', 'countif(view_item_count > 0)') }} as view_to_cart_rate,
    1 - {{ safe_divide('countif(add_to_cart_count > 0)', 'countif(view_item_count > 0)') }} as view_to_cart_dropoff_rate,
    {{ safe_divide('countif(begin_checkout_count > 0)', 'countif(add_to_cart_count > 0)') }} as cart_to_checkout_rate,
    1 - {{ safe_divide('countif(begin_checkout_count > 0)', 'countif(add_to_cart_count > 0)') }} as cart_to_checkout_dropoff_rate,
    {{ safe_divide('countif(purchase_count > 0)', 'countif(begin_checkout_count > 0)') }} as checkout_to_purchase_rate,
    1 - {{ safe_divide('countif(purchase_count > 0)', 'countif(begin_checkout_count > 0)') }} as checkout_to_purchase_dropoff_rate,
    {{ safe_divide('countif(purchase_count > 0)', 'count(*)') }} as overall_purchase_session_rate,
    {{ safe_divide('countif(purchase_count > 0)', 'countif(view_item_count > 0)') }} as view_to_purchase_rate,
    sum(purchase_value) as purchase_value,
    sum(purchase_transaction_count) as purchase_transactions,
    'live_ga4_export' as data_origin
from {{ ref('int_ga4_live_sessions') }}
group by session_date, source, medium, campaign

{% else %}

select null as session_date where false

{% endif %}
