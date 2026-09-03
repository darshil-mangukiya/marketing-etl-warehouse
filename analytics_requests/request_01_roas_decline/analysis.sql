-- REQ-01: governed campaign contribution to paid-social weak return.
select
    campaign_id,
    canonical_campaign_name as campaign_name,
    spend,
    attributed_revenue,
    attributed_revenue / nullif(spend, 0) as attributed_roas,
    greatest(spend - attributed_revenue, 0) as break_even_shortfall
from mart.mart_campaign_performance
where canonical_channel = 'paid_social'
order by break_even_shortfall desc;
