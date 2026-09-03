-- REQ-04: six-method channel-level attribution sensitivity.
select
    channel_name,
    sum(first_touch_revenue) as first_touch_revenue,
    sum(last_touch_revenue) as last_touch_revenue,
    sum(linear_revenue) as linear_revenue,
    sum(u_shaped_revenue) as u_shaped_revenue,
    sum(time_decay_revenue) as time_decay_revenue,
    sum(position_based_revenue) as position_based_revenue
from mart.mart_attribution_model_comparison
group by channel_name
order by linear_revenue desc;
