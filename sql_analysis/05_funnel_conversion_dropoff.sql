-- Business question: Where do leads drop off across the funnel, and which channel-month leaks most?
-- Source: data/exports/demo_mart_funnel_performance.csv (synthetic BI export, local review).
-- Dialect: DuckDB. Reads the generated BI export CSV for reproducible local review.

with funnel as (
    select
        reporting_month,
        normalized_channel,
        cast(total_leads as bigint)           as total_leads,
        cast(mqls as bigint)                  as mqls,
        cast(sales_qualified_leads as bigint) as sales_qualified_leads,
        cast(conversions as bigint)           as conversions
    from read_csv_auto('data/exports/demo_mart_funnel_performance.csv', header=true)
),
rates as (
    select
        reporting_month,
        normalized_channel,
        total_leads,
        sales_qualified_leads,
        conversions,
        round(1 - mqls * 1.0 / nullif(total_leads, 0), 4)                  as lead_to_mql_dropoff,
        round(1 - sales_qualified_leads * 1.0 / nullif(mqls, 0), 4)        as mql_to_sql_dropoff,
        round(1 - conversions * 1.0 / nullif(sales_qualified_leads, 0), 4) as sql_to_close_dropoff,
        round(conversions * 1.0 / nullif(total_leads, 0), 4)              as lead_to_close_rate
    from funnel
)
select
    reporting_month,
    normalized_channel,
    total_leads,
    conversions,
    lead_to_mql_dropoff,
    mql_to_sql_dropoff,
    sql_to_close_dropoff,
    lead_to_close_rate,
    greatest(lead_to_mql_dropoff, mql_to_sql_dropoff, sql_to_close_dropoff) as worst_stage_dropoff,
    case greatest(lead_to_mql_dropoff, mql_to_sql_dropoff, sql_to_close_dropoff)
        when lead_to_mql_dropoff then 'lead_to_mql'
        when mql_to_sql_dropoff then 'mql_to_sql'
        else 'sql_to_close'
    end as biggest_leak_stage
from rates
order by lead_to_close_rate asc, worst_stage_dropoff desc;
