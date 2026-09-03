with attributed as (
    select
        conversion_id,
        attribution_model,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('fact_attribution') }}
    where conversion_id is not null
    group by 1, 2
),
conversion_revenue as (
    select
        conversion_id,
        max(deal_value) as deal_value
    from {{ ref('fact_conversions') }}
    group by 1
)

select
    a.conversion_id,
    a.attribution_model,
    a.attributed_revenue,
    c.deal_value
from attributed a
join conversion_revenue c
    on a.conversion_id = c.conversion_id
where abs(a.attributed_revenue - c.deal_value) > 0.01
