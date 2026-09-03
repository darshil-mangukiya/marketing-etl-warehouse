select 'paid_search' as channel_key, 'Paid Search' as channel_name, 'Paid Media' as channel_group, true as paid_flag
union all select 'paid_social', 'Paid Social', 'Paid Media', true
union all select 'email', 'Email', 'Lifecycle', false
union all select 'organic', 'Organic Search', 'Owned and Earned', false
union all select 'direct', 'Direct', 'Owned and Earned', false
union all select 'referral', 'Referral', 'Owned and Earned', false
union all select 'unknown', 'Unknown', 'Unknown', false
