select
    {{ surrogate_key(["conversion_id", "conversion_date", "coalesce(product, '')"]) }} as fact_revenue_key,
    c.conversion_date as revenue_date,
    cu.customer_key,
    p.product_key,
    ca.campaign_key,
    'sales_conversions' as source_system_key,
    c.deal_value as revenue,
    c.gross_margin,
    c.batch_id as load_batch_id,
    c.updated_at
from {{ ref('stg_sales_conversions') }} c
left join {{ ref('dim_customer') }} cu
    on c.customer_id = cu.customer_id
   and cu.is_current
left join {{ ref('dim_product') }} p
    on c.product = p.product_name
left join {{ ref('dim_campaign') }} ca
    on c.campaign_id = ca.campaign_id
   and ca.is_current
