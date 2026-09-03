create schema if not exists raw;
create schema if not exists staging;
create schema if not exists intermediate;
create schema if not exists warehouse;
create schema if not exists mart;
create schema if not exists semantic;
create schema if not exists ops;

create table if not exists ops.ingestion_logs (
    ingestion_log_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    file_name text not null,
    row_count integer not null,
    accepted_count integer not null,
    rejected_count integer not null,
    load_type text not null check (load_type in ('full', 'incremental', 'unknown')),
    load_status text not null check (load_status in ('success', 'failed', 'skipped')),
    failure_reason text,
    ingestion_time timestamptz not null default now()
);

create table if not exists ops.source_audit (
    source_audit_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    source_file text,
    row_count integer,
    accepted_count integer,
    quality_status text,
    captured_at timestamptz not null default now()
);

create table if not exists ops.rejected_records (
    rejected_record_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    source_file text not null,
    rule_name text not null,
    payload jsonb not null,
    rejected_at timestamptz not null default now()
);

create table if not exists ops.watermarks (
    source_system text primary key,
    watermark_column text not null,
    watermark_value timestamptz not null,
    updated_at timestamptz not null default now()
);

create table if not exists ops.validation_results (
    validation_result_id bigserial primary key,
    batch_id text not null,
    source_system text not null,
    rule_name text not null,
    severity text not null check (severity in ('info', 'warning', 'error')),
    failed_count integer not null,
    status text not null,
    generated_at timestamptz not null default now()
);

create table if not exists warehouse.dim_date (
    date_key integer primary key,
    date_actual date not null unique,
    day_of_week integer not null,
    week_start_date date not null,
    month_start_date date not null,
    month_name text not null,
    quarter_number integer not null,
    year_number integer not null,
    is_weekend boolean not null
);

create table if not exists warehouse.dim_channel (
    channel_key bigint generated always as identity primary key,
    channel_code text not null unique,
    channel_name text not null,
    channel_group text not null,
    paid_flag boolean not null
);

create table if not exists warehouse.dim_source_system (
    source_system_key bigint generated always as identity primary key,
    source_system text not null unique,
    ingestion_method text not null,
    business_owner text not null
);

create table if not exists warehouse.dim_campaign (
    campaign_key bigint generated always as identity primary key,
    campaign_id text not null,
    canonical_campaign_name text not null,
    canonical_channel text not null,
    owner_team text,
    valid_from date not null,
    valid_to date,
    is_current boolean not null default true,
    campaign_hash text not null,
    unique (campaign_id, valid_from)
);

create table if not exists warehouse.dim_customer (
    customer_key bigint generated always as identity primary key,
    customer_id text not null,
    first_lead_date date,
    first_conversion_date date,
    acquisition_channel text,
    customer_segment text,
    valid_from date not null,
    valid_to date,
    is_current boolean not null default true,
    customer_hash text not null,
    unique (customer_id, valid_from)
);

create table if not exists warehouse.dim_region (
    region_key bigint generated always as identity primary key,
    country text not null,
    region text not null,
    sales_territory text not null,
    unique (country, region)
);

create table if not exists warehouse.dim_device (
    device_key bigint generated always as identity primary key,
    device_code text not null unique,
    device_name text not null,
    device_group text not null
);

create table if not exists warehouse.dim_product (
    product_key bigint generated always as identity primary key,
    product_name text not null unique,
    product_family text not null
);

create table if not exists warehouse.dim_sales_rep (
    sales_rep_key bigint generated always as identity primary key,
    rep_id text not null unique,
    sales_team text not null,
    active_flag boolean not null default true
);

create table if not exists warehouse.fact_campaign_performance (
    fact_campaign_performance_key text not null,
    event_date date not null,
    campaign_key bigint,
    channel_key bigint,
    source_system_key bigint,
    region_key bigint,
    impressions bigint,
    clicks bigint,
    spend numeric(18, 2),
    conversions bigint,
    revenue numeric(18, 2),
    source_row_count bigint,
    load_batch_id text,
    updated_at timestamptz not null
);

create table if not exists warehouse.fact_sessions (
    event_date date not null,
    session_id text not null,
    campaign_key bigint,
    channel_key bigint,
    region_key bigint,
    device_key bigint,
    visitor_id text,
    page_views integer,
    session_duration_seconds integer,
    bounce_flag boolean,
    attribution_id text,
    load_batch_id text,
    updated_at timestamptz not null
);

create table if not exists warehouse.fact_leads (
    lead_id text not null,
    created_date date not null,
    customer_key bigint,
    campaign_key bigint,
    channel_key bigint,
    region_key bigint,
    sales_rep_key bigint,
    qualification_stage text,
    lead_score numeric(5, 2),
    attribution_id text,
    cdc_operation text,
    load_batch_id text,
    updated_at timestamptz not null
);

create table if not exists warehouse.fact_conversions (
    conversion_id text not null,
    conversion_date date not null,
    lead_id text,
    customer_key bigint,
    campaign_key bigint,
    product_key bigint,
    deal_value numeric(18, 2),
    gross_margin numeric(18, 2),
    attribution_id text,
    cdc_operation text,
    load_batch_id text,
    updated_at timestamptz not null
);

create table if not exists warehouse.fact_revenue (
    revenue_date date not null,
    customer_key bigint,
    product_key bigint,
    campaign_key bigint,
    source_system_key bigint,
    revenue numeric(18, 2),
    gross_margin numeric(18, 2),
    load_batch_id text,
    loaded_at timestamptz not null default now()
);

create table if not exists warehouse.fact_targets (
    target_month date not null,
    region_key bigint,
    channel_key bigint,
    target_spend numeric(18, 2),
    target_revenue numeric(18, 2),
    target_leads integer,
    target_conversions integer,
    budget_owner text,
    load_batch_id text,
    loaded_at timestamptz not null default now()
);

create table if not exists warehouse.fact_attribution (
    attribution_id text not null,
    conversion_id text,
    customer_key bigint,
    campaign_key bigint,
    channel_key bigint,
    touchpoint_date date,
    conversion_date date,
    attribution_model text not null,
    attribution_weight numeric(8, 6),
    attributed_revenue numeric(18, 2),
    load_batch_id text,
    loaded_at timestamptz not null default now()
);
