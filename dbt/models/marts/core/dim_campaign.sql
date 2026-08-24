with observed_campaigns as (
    select campaign_id, campaign_name, normalized_channel, min(event_date) as first_seen_date
    from {{ ref('int_campaign_spend_unified') }}
    where campaign_id is not null
    group by 1, 2, 3

    union all

    select campaign_id, campaign_name, normalized_channel, min(event_date) as first_seen_date
    from {{ ref('stg_website_analytics') }}
    where campaign_id is not null
    group by 1, 2, 3
),
ranked_names as (
    select
        campaign_id,
        campaign_name,
        normalized_channel,
        first_seen_date,
        row_number() over (partition by campaign_id order by count(*) desc, min(first_seen_date)) as name_rank
    from observed_campaigns
    group by 1, 2, 3, 4
),
mapping_deduped as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by campaign_id
                order by
                    case when valid_to is null then 0 else 1 end,
                    valid_from desc,
                    canonical_campaign_name
            ) as mapping_rank
        from {{ ref('stg_campaign_mapping') }}
    ) m
    where mapping_rank = 1
),
conformed as (
    select
        r.campaign_id,
        {% if target.type == 'duckdb' %}
        coalesce(m.canonical_campaign_name, replace(trim(r.campaign_name), '_', ' '), 'Unknown Campaign') as canonical_campaign_name,
        {% else %}
        coalesce(m.canonical_campaign_name, initcap(replace(trim(r.campaign_name), '_', ' ')), 'Unknown Campaign') as canonical_campaign_name,
        {% endif %}
        coalesce(m.canonical_channel, r.normalized_channel, 'unknown') as canonical_channel,
        coalesce(m.owner_team, 'unmapped') as owner_team,
        coalesce(m.valid_from, r.first_seen_date, date '1900-01-01') as valid_from,
        m.valid_to,
        case when m.valid_to is null then true else false end as is_current
    from ranked_names r
    left join mapping_deduped m
        on r.campaign_id = m.campaign_id
    where r.name_rank = 1
)
select
    {{ surrogate_key(["campaign_id", "canonical_campaign_name", "canonical_channel", "valid_from"]) }} as campaign_key,
    campaign_id,
    canonical_campaign_name,
    canonical_channel,
    owner_team,
    valid_from,
    valid_to,
    is_current,
    {{ surrogate_key(["canonical_campaign_name", "canonical_channel", "owner_team"]) }} as campaign_hash
from conformed
