# ADR 0002: dbt and Dimensional Modeling

## Status

Accepted

## Context

Marketing reporting needs reusable, BI-friendly data products rather than dashboard-specific SQL.

## Decision

Use dbt to model staging, intermediate, core warehouse, and reporting marts. Use conformed dimensions and reusable fact tables for campaign, session, lead, conversion, revenue, target, and attribution analysis.

## Consequences

- BI assets can reuse governed marts and measures.
- dbt tests and docs provide lineage and quality evidence.
- Business logic is centralized instead of duplicated in dashboards.
