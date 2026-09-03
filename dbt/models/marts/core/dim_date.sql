with boundaries as (
    select min(event_date) as min_date, max(event_date) as max_date from {{ ref('int_campaign_daily') }}
    union all
    select min(event_date), max(event_date) from {{ ref('stg_website_analytics') }}
    union all
    select min(created_date), max(created_date) from {{ ref('stg_crm_leads') }}
    union all
    select min(conversion_date), max(conversion_date) from {{ ref('stg_sales_conversions') }}
),
limits as (
    select
        {% if target.type == 'duckdb' %}
        cast(coalesce(min(min_date), current_date - interval '2 years') as date) as min_date,
        cast(coalesce(max(max_date), current_date) as date) as max_date
        {% else %}
        coalesce(min(min_date), current_date - interval '2 years')::date as min_date,
        coalesce(max(max_date), current_date)::date as max_date
        {% endif %}
    from boundaries
),
date_spine as (
    {% if target.type == 'duckdb' %}
    select cast(date_actual as date) as date_actual
    from limits,
    generate_series(min_date, max_date, interval '1 day') as spine(date_actual)
    {% else %}
    select generate_series(min_date, max_date, interval '1 day')::date as date_actual
    from limits
    {% endif %}
)
select
    {% if target.type == 'duckdb' %}
    cast(strftime(date_actual, '%Y%m%d') as integer) as date_key,
    date_actual,
    cast(strftime(date_actual, '%u') as integer) as day_of_week,
    cast(date_trunc('week', date_actual) as date) as week_start_date,
    cast(date_trunc('month', date_actual) as date) as month_start_date,
    strftime(date_actual, '%B') as month_name,
    cast(extract(quarter from date_actual) as integer) as quarter_number,
    cast(extract(year from date_actual) as integer) as year_number,
    cast(strftime(date_actual, '%u') as integer) in (6, 7) as is_weekend
    {% else %}
    to_char(date_actual, 'YYYYMMDD')::integer as date_key,
    date_actual,
    extract(isodow from date_actual)::integer as day_of_week,
    date_trunc('week', date_actual)::date as week_start_date,
    date_trunc('month', date_actual)::date as month_start_date,
    to_char(date_actual, 'Month') as month_name,
    extract(quarter from date_actual)::integer as quarter_number,
    extract(year from date_actual)::integer as year_number,
    extract(isodow from date_actual) in (6, 7) as is_weekend
    {% endif %}
from date_spine
