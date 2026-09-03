select
    {{ surrogate_key(["country", "region"]) }} as region_key,
    country,
    region,
    sales_territory
from {{ ref('stg_region_mapping') }}

union all

select
    {{ surrogate_key(["'UNKNOWN'", "region"]) }} as region_key,
    'UNKNOWN' as country,
    region,
    case
        when region = 'NA' then 'North America'
        when region = 'LATAM' then 'Latin America'
        when region = 'EMEA' then 'Europe'
        when region = 'APAC' then 'Asia Pacific'
        else 'Unknown'
    end as sales_territory
from (
    select 'NA' as region
    union all select 'LATAM'
    union all select 'EMEA'
    union all select 'APAC'
    union all select 'UNKNOWN'
) as regions
