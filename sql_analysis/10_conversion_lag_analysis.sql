-- Business question: How long do conversions take?
-- Dialect: DuckDB. This query reads the generated BI export CSV for reproducible local review.

with base as (
    select *
    from read_csv_auto('data/exports/demo_mart_conversion_lag.csv', header=true)
),
ranked as (
    select
        *,
        row_number() over () as output_rank
    from base
)
select *
from ranked
limit 100;
