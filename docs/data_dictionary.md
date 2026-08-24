# Cloud Upgrade Data Dictionary

The existing generated field catalog remains authoritative for original assets (`catalog/generated/bi_field_dictionary.csv`). This addendum governs new fields.

| Asset | Field | Type/meaning |
|---|---|---|
| ga4_events | event_id | Unique generated event identifier |
| ga4_events | user_pseudo_id / session_id | Generated GA4-style user/session identifiers |
| ga4_events | event_name | Accepted funnel event vocabulary |
| ga4_events | source / medium / campaign | Acquisition dimensions |
| ga4_events | engagement_indicator / conversion_indicator | Integer 0/1 business indicators |
| ga4_events | revenue | Purchase revenue only; zero on non-purchase events |
| mart_marketing_variance_drivers | current_* / prior_* | Current and lagged KPI values at month/channel grain |
| mart_marketing_variance_drivers | primary_driver / secondary_driver | Deterministic diagnostic labels; causal interpretation is not supported |
| mart_campaign_action_center | performance_status / action_priority | Transparent target/quality categorization |
| mart_campaign_action_center | recommended_action / action_reason | Deterministic rule output and explanation |
| mart_campaign_action_center | data_quality_status | Override status that can hold performance action |
| connector result | request_id / rate_limit_remaining / retry_count | Non-secret API observability metadata |
