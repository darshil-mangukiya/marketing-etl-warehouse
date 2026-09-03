# GA4 Analytics Architecture

P2 has two intentionally separate GA4 paths. They are never blended or described as the same provenance.

## Generated event path — locally verified

The local source generates GA4-shaped events including `session_start`, `page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `generate_lead`, and `purchase`, with generated identifiers, timestamps, acquisition fields, product, engagement, and revenue values.

Lineage: `ga4_events` generator/contract → raw lake → `stg_ga4_events` → `int_ga4_sessions` → `mart_ga4_funnel` → local/Power BI-ready exports. This path remains portable across the existing local workflows and does not imply real advertising or business data.

## Project-site path — BigQuery verified

Lineage: `Vercel live site` → `GA4 gtag.js` → `GA4 ecommerce events` → `GA4 Daily BigQuery export` → `analytics_550433518.events_*` → `stg_ga4_live_events` / `stg_ga4_live_ecommerce_items` → `int_ga4_live_sessions` → `mart_ga4_live_funnel` → Power BI / analytics-ready outputs.

The live source is a dbt wildcard relation rather than a fixed dated table. Every model applies a `_TABLE_SUFFIX` date window (14 days by default), runs only for the BigQuery target, and preserves the raw export. This isolation is required because GA4 wildcard tables, nested `event_params`, and repeated `items` are BigQuery-specific.

`stg_ga4_live_events` has one row per event and extracts page/session, engagement, value, transaction, acquisition, device and geography fields. `stg_ga4_live_ecommerce_items` has one row per repeated item for `view_item`, `add_to_cart`, `begin_checkout` and `purchase`. Keeping these grains separate prevents item arrays from inflating event counts.

Curated live models accept only `p2.darshilmangukiya.com`, derived from the `page_location` hostname. Development traffic from `127.0.0.1` and `localhost` remains untouched in raw but is absent from curated outputs. Sessionization uses `user_pseudo_id + ga_session_id` internally and exposes deterministic hashes rather than the raw pseudonymous identifier. The reporting mart contains aggregate metrics only.

## Current evidence boundary

As of 2026-08-20, `events_20260818` and `events_20260819` are available. The second table contains one live-host `view_item` with one valid repeated item: `Signal Starter`, category `Foundation`, USD `24`, quantity `1`. The wildcard source and date predicate incorporated the new table without a code or source-name change.

The refreshed mart has two dated direct-traffic cohorts. The `2026-08-19` cohort has one view-item session and no downstream stage in that session, producing view-to-cart `0.0`, drop-off `1.0` and view-to-purchase `0.0`. The prior cohort contains the cart, checkout and purchase validation. These separate sessions prove collection and modeling at every stage; they do not establish one continuous conversion journey.

The current sample is intentionally tiny and exists to validate collection, nested parsing, filtering, sessionization and funnel logic. It is not suitable for business-performance or causal conclusions.
