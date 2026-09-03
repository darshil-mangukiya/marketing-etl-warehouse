# Source-to-Target Mapping

| Source | Raw Object | Staging Model | Warehouse/Mart Targets | Notes |
|---|---|---|---|---|
| Google Ads API | `raw.google_ads` | `stg_google_ads` | `fact_campaign_performance`, `mart_channel_performance`, `mart_campaign_performance` | Paid search metrics, spend, clicks, conversions, attribution IDs. |
| Facebook Ads API | `raw.facebook_ads` | `stg_facebook_ads` | `fact_campaign_performance`, attribution marts | Paid social metrics with placement and schema drift field. |
| TikTok Ads API | `raw.tiktok_ads` | `stg_tiktok_ads` | `fact_campaign_performance`, attribution marts | Video-view exposure grain normalized into impressions/views. |
| Website Analytics | `raw.website_analytics` | `stg_website_analytics` | `fact_sessions`, `int_customer_journey`, funnel marts | Session, device, country, UTM, and attribution touchpoint data. |
| Generated GA4-style events | `raw.ga4_events` | `stg_ga4_events` | `int_ga4_sessions`, `mart_ga4_funnel` | DuckDB-compatible local path. |
| Project-site GA4 Daily export | `analytics_550433518.events_*` | `stg_ga4_live_events`, `stg_ga4_live_ecommerce_items` | `int_ga4_live_sessions`, `mart_ga4_live_funnel` | Date-filtered export; curated models include only `p2.darshilmangukiya.com` and exclude localhost traffic. |
| CRM Leads | `raw.crm_leads` | `stg_crm_leads` | `fact_leads`, `dim_customer`, funnel marts | CDC flags filter deletes and support incremental updates. |
| Sales Conversions | `raw.sales_conversions` | `stg_sales_conversions` | `fact_conversions`, `fact_revenue`, `fact_attribution`, LTV marts | Deal value, gross margin, product, conversion lag. |
| Marketing Targets | `raw.marketing_targets` | `stg_marketing_targets` | `fact_targets`, `mart_target_vs_actual` | Monthly budget, revenue, lead, and conversion goals. |
| Campaign Mapping | `raw.campaign_mapping` | `stg_campaign_mapping` | `dim_campaign` | Canonical campaign naming and SCD history inputs. |
| Region Mapping | `raw.region_mapping` | `stg_region_mapping` | `dim_region` | Country to reporting region conformance. |
| Channel performance | `mart_channel_performance` | n/a | `mart_marketing_variance_drivers` | Current/prior diagnostic movements for spend, traffic, conversion, revenue, AOV, CAC and ROAS. |
| Campaign performance + targets + quality | governed marts | n/a | `mart_campaign_action_center` | Target-aware deterministic action, reason, priority and quality hold. |
