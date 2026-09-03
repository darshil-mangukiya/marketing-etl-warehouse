select
    reporting_month,
    campaign_id,
    count(*) as row_count
from {{ ref('mart_campaign_action_center') }}
group by reporting_month, campaign_id
having count(*) > 1
