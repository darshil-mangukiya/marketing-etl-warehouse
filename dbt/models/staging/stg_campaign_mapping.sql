select
    cast(campaign_id as {{ string_type() }}) as campaign_id,
    cast(canonical_campaign_name as {{ string_type() }}) as canonical_campaign_name,
    cast(canonical_channel as {{ string_type() }}) as canonical_channel,
    cast(owner_team as {{ string_type() }}) as owner_team,
    case
        when lower(nullif(cast(valid_from as {{ string_type() }}), '')) in ('nan', 'nat', 'none') then null
        else cast(cast(valid_from as {{ string_type() }}) as date)
    end as valid_from,
    case
        when valid_to is null then null
        when lower(nullif(cast(valid_to as {{ string_type() }}), '')) in ('nan', 'nat', 'none') then null
        else cast(cast(valid_to as {{ string_type() }}) as date)
    end as valid_to,
    cast(batch_id as {{ string_type() }}) as batch_id
from {{ source('raw', 'campaign_mapping') }}
