-- Business question: Which recommended actions from the action center should be worked first?
-- Source: data/exports/demo_mart_action_center.csv (synthetic BI export, local review).
-- Dialect: DuckDB. This query reads the generated BI export CSV for reproducible local review.

with actions as (
    select *
    from read_csv_auto('data/exports/demo_mart_action_center.csv', header=true)
),
prioritized as (
    select
        *,
        row_number() over (order by priority asc, action_value desc, due_in_days asc) as work_order
    from actions
)
select *
from prioritized
order by work_order;
