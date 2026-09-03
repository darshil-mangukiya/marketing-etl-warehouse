-- Business question: Which customer segments carry the most value, and how efficiently?
-- Source: data/exports/demo_mart_customer_value.csv (synthetic BI export, local review).
-- Dialect: DuckDB. Reads the generated BI export CSV for reproducible local review.

with customers as (
    select
        customer_id,
        customer_segment,
        cast(purchase_count as bigint)   as purchase_count,
        cast(lifetime_revenue as double) as lifetime_revenue,
        cast(lifetime_margin as double)  as lifetime_margin
    from read_csv_auto('data/exports/demo_mart_customer_value.csv', header=true)
),
by_segment as (
    select
        customer_segment,
        count(*)                        as customer_count,
        sum(lifetime_revenue)           as total_lifetime_revenue,
        sum(lifetime_margin)            as total_lifetime_margin,
        round(avg(lifetime_revenue), 2) as avg_lifetime_revenue,
        round(avg(lifetime_margin), 2)  as avg_lifetime_margin,
        round(avg(purchase_count), 2)   as avg_purchase_count
    from customers
    group by customer_segment
)
select
    customer_segment,
    customer_count,
    total_lifetime_revenue,
    total_lifetime_margin,
    avg_lifetime_revenue,
    avg_lifetime_margin,
    avg_purchase_count,
    round(total_lifetime_margin / nullif(total_lifetime_revenue, 0), 4)                       as margin_rate,
    round(100.0 * total_lifetime_revenue / nullif(sum(total_lifetime_revenue) over (), 0), 1) as revenue_share_pct,
    rank() over (order by total_lifetime_revenue desc)                                        as revenue_rank
from by_segment
order by total_lifetime_revenue desc;
