select *
from {{ ref('mart_channel_performance') }}
where spend < 0
   or impressions < 0
   or clicks < 0
   or leads < 0
   or qualified_leads < 0
   or closed_won_conversions < 0
   or booked_revenue < 0
   or gross_margin < 0
