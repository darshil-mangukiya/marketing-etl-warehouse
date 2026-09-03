select
    reporting_month,
    channel_key,
    channel_name,
    spend,
    booked_revenue,
    gross_margin,
    roas,
    mer,
    cac,
    case
        when spend = 0 then 'no_spend'
        when roas >= 4 and cac <= 500 then 'scale'
        when roas >= 2 then 'maintain'
        when roas < 1 then 'cut_or_fix'
        else 'watch'
    end as budget_recommendation,
    case
        when spend > 0 then gross_margin - spend
        else gross_margin
    end as contribution_after_marketing
from {{ ref('mart_channel_performance') }}
