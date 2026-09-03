{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select session_key
from {{ ref('int_ga4_live_sessions') }}
where (
        first_view_item_at is not null
        and first_add_to_cart_at is not null
        and first_add_to_cart_at < first_view_item_at
    )
    or (
        first_add_to_cart_at is not null
        and first_begin_checkout_at is not null
        and first_begin_checkout_at < first_add_to_cart_at
    )
    or (
        first_begin_checkout_at is not null
        and first_purchase_at is not null
        and first_purchase_at < first_begin_checkout_at
    )

{% else %}

select 1 where false

{% endif %}
