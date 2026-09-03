select *
from {{ ref('mart_target_vs_actual') }}
where target_spend < 0
   or actual_spend < 0
   or target_revenue < 0
   or actual_revenue < 0
   or target_leads < 0
   or actual_leads < 0
   or spend_attainment < 0
   or revenue_attainment < 0
   or lead_attainment < 0
