select
    {{ surrogate_key(["assigned_rep"]) }} as sales_rep_key,
    assigned_rep as rep_id,
    case
        when right(assigned_rep, 1)::integer in (0, 1, 2, 3) then 'commercial'
        when right(assigned_rep, 1)::integer in (4, 5, 6) then 'mid_market'
        else 'enterprise'
    end as sales_team,
    true as active_flag
from (
    select distinct assigned_rep
    from {{ ref('stg_crm_leads') }}
    where assigned_rep is not null
) reps
