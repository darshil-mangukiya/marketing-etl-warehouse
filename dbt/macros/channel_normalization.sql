{% macro normalize_channel(channel_expression) -%}
    case
        when lower({{ channel_expression }}) in ('google ads', 'google_ads', 'paid search', 'paid_search', 'sem') then 'paid_search'
        when lower({{ channel_expression }}) in ('facebook', 'facebook_ads', 'tiktok_ads', 'tik tok', 'paid social', 'paid_social') then 'paid_social'
        when lower({{ channel_expression }}) in ('email', 'lifecycle') then 'email'
        when lower({{ channel_expression }}) in ('organic', 'organic_search') then 'organic'
        when lower({{ channel_expression }}) in ('direct') then 'direct'
        when lower({{ channel_expression }}) in ('referral') then 'referral'
        else 'unknown'
    end
{%- endmacro %}
