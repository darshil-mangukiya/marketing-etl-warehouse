with invalid_windows as (
    select
        campaign_id,
        valid_from,
        valid_to,
        'valid_to_before_valid_from' as issue_type
    from {{ ref('dim_campaign') }}
    where valid_to is not null
      and valid_to < valid_from
),
multiple_current_rows as (
    select
        campaign_id,
        min(valid_from) as valid_from,
        max(valid_to) as valid_to,
        'multiple_current_rows' as issue_type
    from {{ ref('dim_campaign') }}
    where is_current
    group by 1
    having count(*) > 1
)

select * from invalid_windows
union all
select * from multiple_current_rows
