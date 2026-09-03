-- REQ-06: source release decision and comparison with campaign-level hold logic.
select
    source_system,
    source_rows,
    rejected_rows,
    rejected_rows / nullif(source_rows, 0) as rejection_rate,
    failed_count,
    severity,
    monitoring_status,
    case
        when monitoring_status = 'quality_failure' then 'HOLD'
        when monitoring_status = 'quality_warning' then 'REVIEW'
        else 'RELEASE'
    end as recommended_release_decision
from mart.mart_data_quality_monitoring
order by recommended_release_decision, rejection_rate desc;
