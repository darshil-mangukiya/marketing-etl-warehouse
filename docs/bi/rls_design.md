# Power BI Row-Level Security Design

## Scope and truthful status

This repository includes TMDL role definitions in `semantic_layer/powerbi_tmdl/roles.tmdl` and automated static validation. The filters use generated project dimensions. Power BI Desktop **View as role** and Service-side enforcement are deployment checks.

| Role | Intended persona | Filter | Expected access |
|---|---|---|---|
| Executive | VP Marketing / Finance Business Partner | No row filter | All modeled rows |
| Channel Manager | Performance Marketing Manager | `dim_channel[channel_group] = "Paid"` | Paid Search and Paid Social rows through one-direction relationships |
| Regional Manager | Regional marketing manager | `dim_region[region] = "EMEA"` | EMEA target rows through the region relationship |

## Test procedure

1. Import the generated CSVs and apply `relationships.tmdl` and `roles.tmdl` in Power BI Desktop.
2. Use **Modeling > View as** for each role.
3. Confirm Executive totals match the unfiltered reconciliation evidence.
4. Confirm Channel Manager sees only the Paid channel group on related channel/funnel facts.
5. Confirm Regional Manager sees only `EMEA` on region-related target facts.
6. Confirm region filters affect only facts connected through governed relationships.

Static repository tests prove the role names, predicates, referenced columns, and semantic relationships exist. They do not substitute for Desktop or Service runtime validation.
