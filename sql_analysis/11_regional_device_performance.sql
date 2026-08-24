-- Business question: How does performance vary by region and device?
-- Dialect: DuckDB. This query reads the generated BI export CSV for reproducible local review.

with base as (
    select *
    from read_csv_auto('data/exports/demo_mart_regional_performance.csv', header=true)
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
