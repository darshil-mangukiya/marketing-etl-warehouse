with metrics as (
    select
        reporting_month,
        channel_key,
        channel_name,
        spend,
        impressions,
        clicks,
        ctr,
        cpc,
        closed_won_conversions as conversions,
        booked_revenue as revenue,
        {{ safe_divide('booked_revenue', 'closed_won_conversions') }} as aov,
        cac,
        roas
    from {{ ref('mart_channel_performance') }}
),
with_prior as (
    select
        *,
        lag(spend) over (partition by channel_key order by reporting_month) as prior_spend,
        lag(impressions) over (partition by channel_key order by reporting_month) as prior_impressions,
        lag(clicks) over (partition by channel_key order by reporting_month) as prior_clicks,
        lag(ctr) over (partition by channel_key order by reporting_month) as prior_ctr,
        lag(cpc) over (partition by channel_key order by reporting_month) as prior_cpc,
        lag(conversions) over (partition by channel_key order by reporting_month) as prior_conversions,
        lag(revenue) over (partition by channel_key order by reporting_month) as prior_revenue,
        lag(aov) over (partition by channel_key order by reporting_month) as prior_aov,
        lag(cac) over (partition by channel_key order by reporting_month) as prior_cac,
        lag(roas) over (partition by channel_key order by reporting_month) as prior_roas
    from metrics
)
select
    reporting_month,
    channel_key,
    channel_name,
    spend as current_spend,
    prior_spend,
    spend - prior_spend as spend_absolute_variance,
    {{ safe_divide('spend - prior_spend', 'prior_spend') }} as spend_percentage_variance,
    impressions as current_impressions,
    prior_impressions,
    clicks as current_clicks,
    prior_clicks,
    ctr as current_ctr,
    prior_ctr,
    cpc as current_cpc,
    prior_cpc,
    conversions as current_conversions,
    prior_conversions,
    revenue as current_revenue,
    prior_revenue,
    aov as current_aov,
    prior_aov,
    cac as current_cac,
    prior_cac,
    cac - prior_cac as cac_absolute_variance,
    {{ safe_divide('cac - prior_cac', 'prior_cac') }} as cac_percentage_variance,
    roas as current_roas,
    prior_roas,
    roas - prior_roas as roas_absolute_variance,
    {{ safe_divide('roas - prior_roas', 'prior_roas') }} as roas_percentage_variance,
    case
        when prior_roas is null then 'NO_PRIOR_PERIOD'
        when abs({{ safe_divide('revenue - prior_revenue', 'prior_revenue') }}) >= abs({{ safe_divide('spend - prior_spend', 'prior_spend') }}) then 'REVENUE_CHANGE'
        else 'SPEND_CHANGE'
    end as primary_driver,
    case
        when prior_roas is null then 'NO_PRIOR_PERIOD'
        when abs({{ safe_divide('conversions - prior_conversions', 'prior_conversions') }}) >= abs({{ safe_divide('aov - prior_aov', 'prior_aov') }}) then 'CONVERSION_VOLUME'
        else 'AVERAGE_ORDER_VALUE'
    end as secondary_driver,
    case
        when prior_roas is null then 'INFO'
        when abs({{ safe_divide('roas - prior_roas', 'prior_roas') }}) >= 0.25 then 'HIGH'
        when abs({{ safe_divide('roas - prior_roas', 'prior_roas') }}) >= 0.10 then 'MEDIUM'
        else 'LOW'
    end as severity,
    case
        when prior_roas is null then 'Collect another complete period before interpreting change.'
        when roas < prior_roas and revenue < prior_revenue then 'Review conversion volume, attribution coverage, and funnel drop-off.'
        when roas < prior_roas and spend > prior_spend then 'Review bid, audience, placement, CPC, and budget allocation changes.'
        when roas > prior_roas then 'Validate the improvement and identify campaigns suitable for controlled scaling.'
        else 'Monitor the next period and validate source freshness.'
    end as recommended_investigation
from with_prior
