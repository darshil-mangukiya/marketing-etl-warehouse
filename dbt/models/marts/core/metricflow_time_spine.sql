select
    date_actual as date_day
from {{ ref('dim_date') }}
