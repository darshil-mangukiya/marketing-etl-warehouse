select
    event_date,
    campaign_id,
    normalized_channel,
    source_system,
    reporting_region,
    min(campaign_name) as sample_campaign_name,
    sum(exposure_count) as impressions_or_views,
    sum(clicks) as clicks,
    sum(spend) as spend,
    sum(conversions) as platform_conversions,
    count(*) as source_row_count,
    max(updated_at) as updated_at,
    max(batch_id) as batch_id
from {{ ref('int_campaign_spend_unified') }}
group by 1, 2, 3, 4, 5
