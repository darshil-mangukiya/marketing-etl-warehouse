with validation as (
    select
        source_system,
        rule_name,
        severity,
        sum(failed_count) as failed_count,
        max(generated_at) as last_failed_at
    from {{ source('ops', 'validation_results') }}
    group by 1, 2, 3
),
ingestion as (
    select
        source_system,
        max(ingestion_time) as last_ingestion_time,
        count(*) filter (where load_status = 'failed') as failed_loads,
        sum(row_count) as source_rows,
        sum(rejected_count) as rejected_rows
    from {{ source('ops', 'ingestion_logs') }}
    group by 1
)
select
    coalesce(i.source_system, v.source_system) as source_system,
    i.last_ingestion_time,
    i.failed_loads,
    i.source_rows,
    i.rejected_rows,
    v.rule_name,
    v.severity,
    v.failed_count,
    v.last_failed_at,
    case
        {% if target.type == 'duckdb' %}
        when cast(i.last_ingestion_time as timestamp) < current_timestamp - interval '36 hours' then 'freshness_failure'
        {% else %}
        when i.last_ingestion_time < now() - interval '36 hours' then 'freshness_failure'
        {% endif %}
        when i.failed_loads > 0 then 'load_failure'
        when v.severity = 'error' and v.failed_count > 0 then 'quality_failure'
        when v.severity = 'warning' and v.failed_count > 0 then 'quality_warning'
        else 'healthy'
    end as monitoring_status
from ingestion i
full outer join validation v
    on i.source_system = v.source_system
