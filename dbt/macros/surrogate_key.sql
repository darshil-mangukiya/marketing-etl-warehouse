{% macro surrogate_key(columns) -%}
    {%- if target.type == 'bigquery' -%}
    to_hex(md5(cast(concat(
        {%- for column in columns -%}
            coalesce(cast({{ column }} as string), '')
            {%- if not loop.last -%}, '||', {%- endif -%}
        {%- endfor -%}
    ) as bytes)))
    {%- else -%}
    md5(
        concat_ws(
            '||',
            {%- for column in columns -%}
                coalesce(cast({{ column }} as text), '')
                {%- if not loop.last -%},{%- endif -%}
            {%- endfor -%}
        )
    )
    {%- endif -%}
{%- endmacro %}
