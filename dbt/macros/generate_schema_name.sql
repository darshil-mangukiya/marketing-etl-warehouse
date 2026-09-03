{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if target.type == 'bigquery' and custom_schema_name == 'staging' -%}
        {{ env_var('BIGQUERY_STAGING_DATASET', 'marketing_staging') }}
    {%- elif target.type == 'bigquery' and custom_schema_name == 'intermediate' -%}
        {{ env_var('BIGQUERY_STAGING_DATASET', 'marketing_staging') }}
    {%- elif target.type == 'bigquery' and custom_schema_name == 'warehouse' -%}
        {{ env_var('BIGQUERY_WAREHOUSE_DATASET', 'marketing_warehouse') }}
    {%- elif target.type == 'bigquery' and custom_schema_name == 'mart' -%}
        {{ env_var('BIGQUERY_MART_DATASET', 'marketing_mart') }}
    {%- elif custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
