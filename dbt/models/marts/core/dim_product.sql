select
    {{ surrogate_key(["product"]) }} as product_key,
    product as product_name,
    case
        when product in ('Enterprise', 'Marketing Suite') then 'Enterprise'
        when product in ('Growth', 'Commerce Pro') then 'Expansion'
        else 'Entry'
    end as product_family
from (
    select distinct product from {{ ref('stg_sales_conversions') }} where product is not null
) products
