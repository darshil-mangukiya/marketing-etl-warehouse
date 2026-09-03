# Relationship Map

- dim_channel.channel_key -> mart_channel_performance.channel_key | many-to-one | single
- dim_channel.channel_key -> mart_funnel_performance.channel_key | many-to-one | single
- dim_date.date_day -> mart_channel_performance.reporting_month | many-to-one | single
- dim_date.date_day -> mart_funnel_performance.reporting_month | many-to-one | single
- dim_date.date_day -> mart_target_vs_actual.target_month | many-to-one | single
- dim_campaign.campaign_id -> mart_campaign_performance.campaign_id | many-to-one | single
- dim_region.region -> mart_target_vs_actual.region | many-to-one | single
- dim_date.date_day -> mart_ga4_funnel.event_date | many-to-one | single
- dim_campaign.campaign_id -> mart_ga4_funnel.campaign_id | many-to-one | single
- dim_channel.channel_key -> mart_marketing_variance_drivers.channel_key | many-to-one | single
- dim_campaign.campaign_id -> mart_campaign_action_center.campaign_id | many-to-one | single
