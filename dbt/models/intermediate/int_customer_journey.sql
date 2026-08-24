with sessions as (
    select
        session_id,
        event_date as touchpoint_date,
        visitor_id,
        campaign_id,
        campaign_name,
        normalized_channel,
        country,
        device,
        attribution_id
    from {{ ref('stg_website_analytics') }}
),
leads as (
    select
        lead_id,
        customer_id,
        created_date as lead_created_date,
        campaign_id as lead_campaign_id,
        normalized_channel as lead_channel,
        qualification_stage,
        lead_score,
        assigned_rep,
        region,
        attribution_id
    from {{ ref('stg_crm_leads') }}
),
conversions as (
    select
        conversion_id,
        lead_id,
        customer_id,
        conversion_date,
        campaign_id as conversion_campaign_id,
        product,
        deal_value,
        gross_margin,
        attribution_id
    from {{ ref('stg_sales_conversions') }}
)
select
    coalesce(s.attribution_id, l.attribution_id, c.attribution_id) as attribution_id,
    s.session_id,
    s.touchpoint_date,
    s.visitor_id,
    coalesce(s.campaign_id, l.lead_campaign_id, c.conversion_campaign_id) as campaign_id,
    coalesce(s.normalized_channel, l.lead_channel) as normalized_channel,
    l.lead_id,
    l.customer_id,
    l.lead_created_date,
    l.qualification_stage,
    l.lead_score,
    l.assigned_rep,
    l.region,
    c.conversion_id,
    c.conversion_date,
    c.product,
    c.deal_value,
    c.gross_margin,
    case
        when c.conversion_date is not null and l.lead_created_date is not null
            then c.conversion_date - l.lead_created_date
        else null
    end as lead_to_conversion_days
from sessions s
full outer join leads l
    on s.attribution_id = l.attribution_id
full outer join conversions c
    on coalesce(l.lead_id, 'missing') = c.lead_id
    or coalesce(l.attribution_id, s.attribution_id) = c.attribution_id
