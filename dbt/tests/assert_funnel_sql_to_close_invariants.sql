select *
from {{ ref('mart_funnel_performance') }}
where sales_qualified_leads < 0
   or conversions < 0
   or conversions > sales_qualified_leads
   or sql_to_close_rate < 0
   or sql_to_close_rate > 1
   or (sales_qualified_leads = 0 and conversions <> 0)
