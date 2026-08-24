{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select item_event_key
from {{ ref('stg_ga4_live_ecommerce_items') }}
where event_name not in ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
    or price < 0
    or quantity <= 0

{% else %}

select 1 where false

{% endif %}
