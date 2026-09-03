with customer_base as (
    select
        customer_id,
        min(created_date) as first_lead_date,
        null::date as first_conversion_date,
        min(normalized_channel) as acquisition_channel,
        0::numeric as lifetime_value
    from {{ ref('stg_crm_leads') }}
    where customer_id is not null
    group by 1

    union all

    select
        customer_id,
        null::date as first_lead_date,
        min(conversion_date) as first_conversion_date,
        null::text as acquisition_channel,
        sum(deal_value) as lifetime_value
    from {{ ref('stg_sales_conversions') }}
    where customer_id is not null
    group by 1
),
rolled as (
    select
        customer_id,
        min(first_lead_date) as first_lead_date,
        min(first_conversion_date) as first_conversion_date,
        coalesce(min(acquisition_channel), 'unknown') as acquisition_channel,
        sum(lifetime_value) as lifetime_value
    from customer_base
    group by 1
)
select
    {{ surrogate_key(["customer_id", "coalesce(first_lead_date, date '1900-01-01')", "coalesce(first_conversion_date, date '1900-01-01')"]) }} as customer_key,
    customer_id,
    first_lead_date,
    first_conversion_date,
    acquisition_channel,
    case
        when lifetime_value >= 25000 then 'enterprise_value'
        when lifetime_value >= 8000 then 'mid_market_value'
        when lifetime_value > 0 then 'smb_value'
        else 'pre_conversion'
    end as customer_segment,
    coalesce(first_lead_date, first_conversion_date, current_date) as valid_from,
    null::date as valid_to,
    true as is_current,
    {{ surrogate_key(["customer_id", "coalesce(acquisition_channel, '')"]) }} as customer_hash
from rolled
