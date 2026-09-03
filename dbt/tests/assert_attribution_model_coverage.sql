with model_counts as (
    select
        conversion_id,
        count(distinct attribution_model) as attribution_model_count
    from {{ ref('fact_attribution') }}
    where conversion_id is not null
    group by 1
)

select *
from model_counts
where attribution_model_count <> 6
