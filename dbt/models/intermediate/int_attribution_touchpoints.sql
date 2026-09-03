with touchpoints as (
    select
        attribution_id,
        session_id,
        event_date as touchpoint_date,
        campaign_id,
        normalized_channel,
        'website_session' as touchpoint_type
    from {{ ref('stg_website_analytics') }}
    where attribution_id is not null

    union all

    select
        attribution_id,
        cast(null as {{ string_type() }}) as session_id,
        event_date as touchpoint_date,
        campaign_id,
        normalized_channel,
        'paid_media_click' as touchpoint_type
    from {{ ref('int_campaign_spend_unified') }}
    where attribution_id is not null
),
conversions as (
    select
        conversion_id,
        customer_id,
        attribution_id,
        campaign_id as conversion_campaign_id,
        conversion_date,
        deal_value
    from {{ ref('stg_sales_conversions') }}
),
eligible as (
    select
        t.*,
        c.conversion_id,
        c.customer_id,
        c.conversion_date,
        c.deal_value,
        greatest({{ date_diff_days('c.conversion_date', 't.touchpoint_date') }}, 0) as days_to_conversion,
        row_number() over (
            partition by c.conversion_id
            order by t.touchpoint_date asc
        ) as first_touch_rank,
        row_number() over (
            partition by c.conversion_id
            order by t.touchpoint_date desc
        ) as last_touch_rank,
        count(*) over (partition by c.conversion_id) as touchpoint_count
    from touchpoints t
    join conversions c
        on t.attribution_id = c.attribution_id
       and t.touchpoint_date <= c.conversion_date
       and t.touchpoint_date >= {{ subtract_days('c.conversion_date', var("lookback_days_for_late_arrivals")) }}
)
,
weighted as (
    select
        *,
        power(0.5, cast(days_to_conversion as numeric) / 7.0) as raw_time_decay_weight
    from eligible
),
normalized as (
    select
        *,
        sum(raw_time_decay_weight) over (partition by conversion_id) as total_time_decay_weight
    from weighted
)
select
    {{ surrogate_key(["conversion_id", "coalesce(session_id, '')", "touchpoint_date", "touchpoint_type"]) }} as attribution_touchpoint_key,
    *,
    case when first_touch_rank = 1 then 1.0 else 0.0 end as first_touch_weight,
    case when last_touch_rank = 1 then 1.0 else 0.0 end as last_touch_weight,
    case when touchpoint_count > 0 then 1.0 / touchpoint_count else 0.0 end as linear_weight,
    case
        when touchpoint_count = 1 then 1.0
        when touchpoint_count = 2 then 0.5
        when first_touch_rank = 1 or last_touch_rank = 1 then 0.4
        else 0.2 / nullif(touchpoint_count - 2, 0)
    end as u_shaped_weight,
    case
        when touchpoint_count = 1 then 1.0
        when touchpoint_count = 2 then 0.5
        when first_touch_rank = 1 then 0.3
        when last_touch_rank = 1 then 0.3
        else 0.4 / nullif(touchpoint_count - 2, 0)
    end as position_based_weight,
    raw_time_decay_weight / nullif(total_time_decay_weight, 0) as time_decay_weight
from normalized
