select
    cast(country as {{ string_type() }}) as country,
    cast(region as {{ string_type() }}) as region,
    cast(sales_territory as {{ string_type() }}) as sales_territory,
    cast(batch_id as {{ string_type() }}) as batch_id
from {{ source('raw', 'region_mapping') }}
