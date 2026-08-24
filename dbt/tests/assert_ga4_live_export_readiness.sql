{{ config(enabled=target.type == 'bigquery', severity='warn', tags=['ga4_live']) }}

{% if target.type == 'bigquery' %}

select
    count(*) as live_event_count,
    max(event_date) as latest_event_date
from {{ ref('stg_ga4_live_events') }}
having count(*) = 0
    or max(event_date) < date_sub(
        current_date('{{ var("ga4_property_timezone", "America/Los_Angeles") }}'),
        interval 3 day
    )

{% else %}

select 1 where false

{% endif %}
