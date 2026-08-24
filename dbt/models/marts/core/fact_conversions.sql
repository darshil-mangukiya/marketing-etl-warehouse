{{ config(materialized='incremental', unique_key='conversion_id', indexes=[{'columns': ['conversion_date']}, {'columns': ['lead_id']}]) }}

select
    c.conversion_id,
    c.conversion_date,
    c.lead_id,
    cu.customer_key,
    ca.campaign_key,
    p.product_key,
    c.deal_value,
    c.gross_margin,
    c.attribution_id,
    c.cdc_operation,
    c.batch_id as load_batch_id,
    c.updated_at
from {{ ref('stg_sales_conversions') }} c
left join {{ ref('dim_customer') }} cu
    on c.customer_id = cu.customer_id
   and cu.is_current
left join {{ ref('dim_campaign') }} ca
    on c.campaign_id = ca.campaign_id
   and ca.is_current
left join {{ ref('dim_product') }} p
    on c.product = p.product_name
{% if is_incremental() %}
where c.updated_at >= (select coalesce(max(target.updated_at), timestamp '1900-01-01') from {{ this }} as target)
{% endif %}
