select *
from {{ ref('fact_campaign_performance') }}
where clicks > impressions
   or spend < 0
   or conversions < 0
