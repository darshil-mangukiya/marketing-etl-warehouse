select
    event_date,
    source,
    medium,
    campaign_id,
    campaign,
    device_category,
    count(distinct case when event_name = 'session_start' then session_id end) as sessions,
    count(distinct case when event_name = 'page_view' then event_id end) as page_views,
    count(distinct case when event_name = 'view_item' then event_id end) as item_views,
    count(distinct case when event_name = 'add_to_cart' then event_id end) as add_to_carts,
    count(distinct case when event_name = 'begin_checkout' then event_id end) as checkouts,
    count(distinct case when event_name = 'generate_lead' then event_id end) as leads,
    count(distinct case when event_name = 'purchase' then event_id end) as purchases,
    sum(case when event_name = 'purchase' then revenue else 0 end) as purchase_revenue
from {{ ref('stg_ga4_events') }}
group by event_date, source, medium, campaign_id, campaign, device_category
