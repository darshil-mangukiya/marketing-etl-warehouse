{% macro month_start(column_name) -%}
    {%- if target.type == 'bigquery' -%}
        date_trunc(cast({{ column_name }} as date), month)
    {%- else -%}
        cast(date_trunc('month', {{ column_name }}) as date)
    {%- endif -%}
{%- endmacro %}

{% macro safe_divide(numerator, denominator) -%}
    {%- if target.type == 'bigquery' -%}
        safe_divide({{ numerator }}, {{ denominator }})
    {%- else -%}
        {{ numerator }} / nullif({{ denominator }}, 0)
    {%- endif -%}
{%- endmacro %}

{% macro count_when(condition) -%}
    sum(case when {{ condition }} then 1 else 0 end)
{%- endmacro %}

{% macro string_type() -%}
    {%- if target.type == 'bigquery' -%}string{%- else -%}text{%- endif -%}
{%- endmacro %}

{% macro numeric_type(precision, scale) -%}
    {%- if target.type == 'bigquery' -%}numeric{%- else -%}numeric({{ precision }}, {{ scale }}){%- endif -%}
{%- endmacro %}

{% macro date_diff_days(later_date, earlier_date) -%}
    {%- if target.type == 'bigquery' -%}
        date_diff({{ later_date }}, {{ earlier_date }}, day)
    {%- else -%}
        {{ later_date }} - {{ earlier_date }}
    {%- endif -%}
{%- endmacro %}

{% macro subtract_days(date_expression, day_count) -%}
    {%- if target.type == 'bigquery' -%}
        date_sub({{ date_expression }}, interval {{ day_count }} day)
    {%- else -%}
        {{ date_expression }} - interval '{{ day_count }} days'
    {%- endif -%}
{%- endmacro %}
