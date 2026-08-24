with revenue as (
    select
        customer_key,
        min(revenue_date) as first_revenue_date,
        count(*) as purchase_count,
        sum(revenue) as lifetime_revenue,
        sum(gross_margin) as lifetime_margin
    from {{ ref('fact_revenue') }}
    group by 1
),
acquisition_spend as (
    select
        ca.canonical_channel as acquisition_channel,
        sum(f.spend) as spend
    from {{ ref('fact_campaign_performance') }} f
    left join {{ ref('dim_campaign') }} ca
        on f.campaign_key = ca.campaign_key
    group by 1
)
select
    c.customer_key,
    c.customer_id,
    c.customer_segment,
    c.acquisition_channel,
    c.first_lead_date,
    r.first_revenue_date,
    r.purchase_count,
    coalesce(r.lifetime_revenue, 0) as lifetime_revenue,
    coalesce(r.lifetime_margin, 0) as lifetime_margin,
    coalesce(r.lifetime_revenue, 0) / nullif(r.purchase_count, 0) as average_order_value,
    s.spend as channel_spend_reference
from {{ ref('dim_customer') }} c
left join revenue r
    on c.customer_key = r.customer_key
left join acquisition_spend s
    on c.acquisition_channel = s.acquisition_channel
