with leads as (
    select
        date_trunc('month', created_date)::date as reporting_month,
        channel_key,
        count(distinct lead_id) as total_leads,
        count(distinct case when qualification_stage = 'new' then lead_id end) as new_leads,
        count(distinct case when qualification_stage = 'marketing_qualified' then lead_id end) as mqls,
        count(distinct case when qualification_stage = 'sales_accepted' then lead_id end) as sals,
        count(distinct case when qualification_stage = 'sales_qualified' then lead_id end) as sqls,
        count(distinct case when qualification_stage = 'disqualified' then lead_id end) as disqualified_leads
    from {{ ref('fact_leads') }}
    group by 1, 2
),
sql_cohort as (
    select
        lead_id,
        min(created_date) as created_date,
        min(channel_key) as channel_key
    from {{ ref('fact_leads') }}
    where qualification_stage = 'sales_qualified'
    group by 1
),
conversions as (
    select
        date_trunc('month', l.created_date)::date as reporting_month,
        l.channel_key,
        count(distinct c.lead_id) as conversions,
        sum(deal_value) as revenue,
        avg(conversion_date - l.created_date) as avg_conversion_lag_days
    from {{ ref('fact_conversions') }} c
    inner join sql_cohort l
        on c.lead_id = l.lead_id
    group by 1, 2
)
select
    coalesce(l.reporting_month, c.reporting_month) as reporting_month,
    coalesce(l.channel_key, c.channel_key) as channel_key,
    ch.channel_name,
    coalesce(l.total_leads, 0) as total_leads,
    coalesce(l.new_leads, 0) as new_leads,
    coalesce(l.mqls, 0) as mqls,
    coalesce(l.sals, 0) as sales_accepted_leads,
    coalesce(l.sqls, 0) as sales_qualified_leads,
    coalesce(l.disqualified_leads, 0) as disqualified_leads,
    coalesce(c.conversions, 0) as conversions,
    coalesce(c.revenue, 0) as revenue,
    c.avg_conversion_lag_days,
    coalesce(l.mqls, 0)::numeric / nullif(l.total_leads, 0) as lead_to_mql_rate,
    coalesce(l.sqls, 0)::numeric / nullif(l.mqls, 0) as mql_to_sql_rate,
    coalesce(c.conversions, 0)::numeric / nullif(l.sqls, 0) as sql_to_close_rate
from leads l
full outer join conversions c
    on l.reporting_month = c.reporting_month
   and l.channel_key = c.channel_key
left join {{ ref('dim_channel') }} ch
    on coalesce(l.channel_key, c.channel_key) = ch.channel_key
