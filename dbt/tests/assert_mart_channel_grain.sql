select
    reporting_month,
    channel_key,
    count(*) as row_count
from {{ ref('mart_channel_performance') }}
group by 1, 2
having count(*) > 1
