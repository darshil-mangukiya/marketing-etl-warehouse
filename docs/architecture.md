# Architecture Summary

## Platform Layers

```mermaid
flowchart TB
    subgraph Source["Source Systems"]
        GA["Google Ads API"]
        FB["Facebook Ads API"]
        TT["TikTok Ads API"]
        WEB["Website Analytics Files"]
        CRM["CRM Leads CDC Files"]
        SALES["Sales Conversion Events"]
        TARGETS["Marketing Targets"]
        REF["Reference Mappings"]
    end

    subgraph Ingest["Ingestion Layer"]
        CLIENTS["API + File Clients"]
        VALIDATE["Schema + Quality Validation"]
        AUDIT["Audit Logs + Metadata"]
        WM["Watermarks + Processed File State"]
    end

    subgraph Lake["Local S3 Simulation"]
        RAW["raw zone"]
        PROC["processed zone"]
        CUR["curated zone"]
    end

    subgraph Warehouse["Warehouse + Transformation"]
        PGRAW["PostgreSQL raw schema"]
        STG["dbt staging"]
        INT["dbt intermediate"]
        WH["Dimensional warehouse"]
        MART["Reporting marts"]
    end

    subgraph BI["Semantic + Reporting"]
        EXPORTS["Power BI-ready CSV exports"]
        KPI["KPI and DAX catalog"]
        DASH["Dashboard page specs"]
    end

    Source --> CLIENTS --> VALIDATE --> RAW
    VALIDATE --> AUDIT
    VALIDATE --> WM
    RAW --> PGRAW --> STG --> INT --> WH --> MART --> EXPORTS
    MART --> KPI --> DASH
```

## Engineering Design Choices

- Generated sources include dirty data, late-arriving records, schema drift, duplicate IDs, null spend, and attribution ambiguity.
- The ingestion layer writes audit logs, source summaries, validation reports, rejected rows, and watermarks.
- dbt separates source cleaning, cross-source conformance, dimensional facts/dimensions, and BI marts.
- Incremental facts use `updated_at` filters to support idempotent reruns and late-arriving updates.
- The semantic layer documents business definitions before dashboard creation, reducing metric drift.

## GCP extension

The local architecture remains the default reproducible path. GCS, BigQuery, dbt-bigquery, empty Secret Manager containers, and the project-site GA4 Daily export are also verified with small controlled workloads, as documented in `docs/cloud_architecture.md` and `docs/P2_LIVE_GCP_VALIDATION.md`. Google Ads, Meta Ads, TikTok Ads, and Power BI Service require separate authorization or deployment.
