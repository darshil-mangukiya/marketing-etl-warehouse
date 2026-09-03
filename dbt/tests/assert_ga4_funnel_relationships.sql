select *
from {{ ref('mart_ga4_funnel') }}
where purchase_revenue < 0
