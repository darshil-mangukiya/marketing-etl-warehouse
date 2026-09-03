with model_weights as (
    select
        conversion_id,
        attribution_model,
        sum(attribution_weight) as attribution_weight_sum
    from {{ ref('fact_attribution') }}
    where conversion_id is not null
    group by 1, 2
)

select *
from model_weights
where attribution_weight_sum < 0.999
   or attribution_weight_sum > 1.001
