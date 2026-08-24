select 'google_ads' as source_system_key, 'Google Ads' as source_system_name, 'REST API' as ingestion_method, 'performance_marketing' as business_owner
union all select 'facebook_ads', 'Facebook Ads', 'REST API', 'performance_marketing'
union all select 'tiktok_ads', 'TikTok Ads', 'REST API', 'performance_marketing'
union all select 'website_analytics', 'Website Analytics', 'batch file', 'growth_analytics'
union all select 'crm_leads', 'CRM Leads', 'batch file with CDC flags', 'revenue_operations'
union all select 'sales_conversions', 'Sales Conversions', 'JSON event file with CDC flags', 'sales_operations'
union all select 'marketing_targets', 'Marketing Targets', 'managed file', 'finance'
