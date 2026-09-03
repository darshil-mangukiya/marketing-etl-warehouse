select *
from {{ ref('mart_campaign_action_center') }}
where (campaign_id is null or campaign_id = '')
  and (recommended_action <> 'DATA QUALITY HOLD' or data_quality_status <> 'HOLD')
