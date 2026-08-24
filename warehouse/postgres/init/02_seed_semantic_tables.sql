do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'warehouse'
          and table_name = 'dim_channel'
          and column_name = 'channel_code'
    ) then
        insert into warehouse.dim_channel (channel_code, channel_name, channel_group, paid_flag)
        values
            ('paid_search', 'Paid Search', 'Paid Media', true),
            ('paid_social', 'Paid Social', 'Paid Media', true),
            ('email', 'Email', 'Lifecycle', false),
            ('organic', 'Organic Search', 'Owned and Earned', false),
            ('direct', 'Direct', 'Owned and Earned', false),
            ('referral', 'Referral', 'Owned and Earned', false)
        on conflict (channel_code) do nothing;
    end if;
end $$;

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'warehouse'
          and table_name = 'dim_source_system'
          and column_name = 'source_system'
    ) then
        insert into warehouse.dim_source_system (source_system, ingestion_method, business_owner)
        values
            ('google_ads', 'REST API', 'performance_marketing'),
            ('facebook_ads', 'REST API', 'performance_marketing'),
            ('tiktok_ads', 'REST API', 'performance_marketing'),
            ('website_analytics', 'batch file', 'growth_analytics'),
            ('crm_leads', 'batch file with CDC flags', 'revenue_operations'),
            ('sales_conversions', 'JSON event file with CDC flags', 'sales_operations'),
            ('marketing_targets', 'managed file', 'finance')
        on conflict (source_system) do nothing;
    end if;
end $$;

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'warehouse'
          and table_name = 'dim_device'
          and column_name = 'device_code'
    ) then
        insert into warehouse.dim_device (device_code, device_name, device_group)
        values
            ('desktop', 'Desktop', 'Web'),
            ('mobile', 'Mobile', 'Mobile'),
            ('tablet', 'Tablet', 'Mobile'),
            ('unknown', 'Unknown', 'Unknown')
        on conflict (device_code) do nothing;
    end if;
end $$;
