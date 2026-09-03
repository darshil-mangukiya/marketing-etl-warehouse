{{ config(enabled=target.type == 'bigquery', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select event_key, hostname
from {{ ref('stg_ga4_live_events') }}
where hostname != lower('{{ var("ga4_live_hostname", "p2.darshilmangukiya.com") }}')
    or hostname in ('127.0.0.1', 'localhost')

{% else %}

select 1 where false

{% endif %}
