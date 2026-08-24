# BigQuery Query and Cost Optimization

## Scope

The review covers four representative live-GA4 workloads. The current models already implement the material optimizations: `_TABLE_SUFFIX` pruning, explicit projections, early event filtering, a single repeated-item `UNNEST`, aggregation after staging, and a 100 MiB per-query ceiling.

| Query/model | Baseline | Optimization/current pattern | Before bytes | After bytes | Reduction | Duration | Correctness validation |
|---|---|---|---:|---:|---:|---|---|
| GA4 wildcard event-count comparison | Unrestricted `events_*` wildcard | `_TABLE_SUFFIX BETWEEN '20260818' AND '20260819'` | 619 | 587 | 32 bytes / 5.17% | Dry run; not executed | Same grouped fields and aggregation; only table boundary changed |
| `stg_ga4_live_events` | Potential wide raw event scan | Explicit columns, date suffix, single event-parameter extraction layer, hostname filter | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | Live selector previously passed 34/34 operations |
| `stg_ga4_live_ecommerce_items` | Repeated items could inflate event grain | Ecommerce event predicate before one `UNNEST(items)`; item grain isolated | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | Item uniqueness, quantity, hostname and event-name tests |
| `int_ga4_live_sessions` → `mart_ga4_live_funnel` | Repeated event scans could duplicate session logic | Reuse staged view, aggregate once to session grain, then once to reporting grain | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | Session keys/rates/sequence tests and observed live reconciliation |

The two event-count estimates were BigQuery dry runs on 2026-08-21. Both billed zero bytes. The small absolute reduction reflects the two-table export; the pruning pattern matters as daily tables accumulate.

## Findings

- Partition/table pruning: PASS — all live wildcard source models call `ga4_live_suffix_predicate()` with a 14-day default lookback.
- Wildcard scans without date limits in curated models: none.
- `SELECT *`: none in the four reviewed models.
- Repeated `UNNEST`: one item-array expansion in the dedicated item model.
- Join/cardinality risk: no joins in the reviewed live chain; event, item and session grains remain separate.
- Aggregation pushdown: event filters precede item expansion; sessions precede funnel aggregation.
- Cost guardrail: 104,857,600 maximum bytes per query remains documented and tested by the controlled execution workflow.

Recorded live validation totals remain unchanged: 1,060,135 cumulative bytes processed and 985,661,440 bytes billed across the documented GA4 validation runs. This optimization review used dry runs and did not execute an additional query.
