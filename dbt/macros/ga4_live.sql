{% macro ga4_event_param_string(param_name, params_column='event_params') -%}
(
    select coalesce(
        event_param.value.string_value,
        cast(event_param.value.int_value as string),
        cast(event_param.value.double_value as string),
        cast(event_param.value.float_value as string)
    )
    from unnest({{ params_column }}) as event_param
    where event_param.key = '{{ param_name }}'
    limit 1
)
{%- endmacro %}

{% macro ga4_event_param_numeric(param_name, params_column='event_params') -%}
(
    select coalesce(
        event_param.value.double_value,
        event_param.value.float_value,
        cast(event_param.value.int_value as float64),
        safe_cast(event_param.value.string_value as float64)
    )
    from unnest({{ params_column }}) as event_param
    where event_param.key = '{{ param_name }}'
    limit 1
)
{%- endmacro %}

{% macro ga4_live_suffix_predicate() -%}
_table_suffix between
    format_date(
        '%Y%m%d',
        date_sub(
            current_date('{{ var("ga4_property_timezone", "America/Los_Angeles") }}'),
            interval {{ var('ga4_live_lookback_days', 14) }} day
        )
    )
    and format_date(
        '%Y%m%d',
        current_date('{{ var("ga4_property_timezone", "America/Los_Angeles") }}')
    )
{%- endmacro %}
