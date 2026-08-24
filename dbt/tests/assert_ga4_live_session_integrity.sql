{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select session_key
from {{ ref('int_ga4_live_sessions') }}
where event_count <= 0
    or page_view_count < 0
    or view_item_count < 0
    or add_to_cart_count < 0
    or begin_checkout_count < 0
    or purchase_count < 0
    or engagement_time_msec < 0
    or purchase_value < 0

{% else %}

select 1 where false

{% endif %}
