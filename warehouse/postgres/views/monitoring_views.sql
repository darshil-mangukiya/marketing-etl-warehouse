create or replace view ops.vw_source_health as
select
    source_system,
    max(ingestion_time) as last_ingestion_time,
    count(*) filter (where load_status = 'success') as successful_loads,
    count(*) filter (where load_status = 'failed') as failed_loads,
    sum(row_count) as total_rows_seen,
    sum(rejected_count) as total_rejected_rows,
    case
        when max(ingestion_time) < now() - interval '36 hours' then 'stale'
        when count(*) filter (where load_status = 'failed') > 0 then 'degraded'
        else 'healthy'
    end as health_status
from ops.ingestion_logs
group by source_system;

create or replace view ops.vw_validation_failure_summary as
select
    source_system,
    rule_name,
    severity,
    date_trunc('day', generated_at) as validation_day,
    sum(failed_count) as failed_count
from ops.validation_results
group by source_system, rule_name, severity, date_trunc('day', generated_at);

create or replace view mart.vw_pipeline_observability as
select
    h.source_system,
    h.last_ingestion_time,
    h.successful_loads,
    h.failed_loads,
    h.total_rows_seen,
    h.total_rejected_rows,
    h.health_status,
    w.watermark_value
from ops.vw_source_health h
left join ops.watermarks w
    on h.source_system = w.source_system;
