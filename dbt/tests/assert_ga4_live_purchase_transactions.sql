{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

with purchases as (
    select event_key, transaction_id, value
    from {{ ref('stg_ga4_live_events') }}
    where event_name = 'purchase'
),

invalid_transactions as (
    select transaction_id
    from purchases
    group by transaction_id
    having transaction_id is null or count(*) > 1
)

select purchases.event_key
from purchases
left join invalid_transactions using (transaction_id)
where invalid_transactions.transaction_id is not null
    or purchases.transaction_id is null
    or purchases.value < 0

{% else %}

select 1 where false

{% endif %}
