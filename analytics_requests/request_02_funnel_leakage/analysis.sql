-- REQ-02: stage leakage by channel for non-empty lead cohorts.
select
    reporting_month,
    channel_key as channel,
    total_leads,
    mqls,
    sales_qualified_leads as sqls,
    conversions,
    total_leads - mqls as lead_to_mql_drop,
    mqls - sales_qualified_leads as mql_to_sql_drop,
    greatest(sales_qualified_leads - conversions, 0) as sql_to_close_drop
from mart.mart_funnel_performance
where total_leads > 0
order by total_leads desc;
