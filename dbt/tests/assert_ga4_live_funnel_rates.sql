{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select session_date, source, medium, campaign
from {{ ref('mart_ga4_live_funnel') }}
where sessions < 0
    or users < 0
    or engaged_sessions < 0
    or view_item_sessions < 0
    or add_to_cart_sessions < 0
    or begin_checkout_sessions < 0
    or purchase_sessions < 0
    or coalesce(view_to_cart_rate not between 0 and 1, false)
    or coalesce(cart_to_checkout_rate not between 0 and 1, false)
    or coalesce(checkout_to_purchase_rate not between 0 and 1, false)
    or coalesce(overall_purchase_session_rate not between 0 and 1, false)
    or coalesce(view_to_purchase_rate not between 0 and 1, false)

{% else %}

select 1 where false

{% endif %}
