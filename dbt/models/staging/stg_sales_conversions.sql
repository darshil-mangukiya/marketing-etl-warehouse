select
    cast(conversion_id as {{ string_type() }}) as conversion_id,
    cast(lead_id as {{ string_type() }}) as lead_id,
    cast(customer_id as {{ string_type() }}) as customer_id,
    cast(created_at as date) as created_date,
    cast(conversion_date as date) as conversion_date,
    cast(product as {{ string_type() }}) as product,
    cast(deal_value as {{ numeric_type(18, 2) }}) as deal_value,
    cast(gross_margin as {{ numeric_type(18, 2) }}) as gross_margin,
    cast(currency as {{ string_type() }}) as currency,
    cast(attribution_id as {{ string_type() }}) as attribution_id,
    cast(campaign_id as {{ string_type() }}) as campaign_id,
    cast(cdc_operation as {{ string_type() }}) as cdc_operation,
    cast(batch_id as {{ string_type() }}) as batch_id,
    cast(updated_at as timestamp) as updated_at,
    cast(source_system as {{ string_type() }}) as source_system
from {{ source('raw', 'sales_conversions') }}
where coalesce(cdc_operation, 'I') <> 'D'
