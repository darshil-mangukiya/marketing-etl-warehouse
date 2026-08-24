# P2 Live GCP Validation

Validated: 2026-08-18 (America/Los_Angeles)  
Project: `p2-marketing-analytics-505916`  
Requested region: `us-central1`  
Terraform directory: `terraform/`

## LIVE PROVISIONED — 2026-08-18

The saved Terraform plan was applied successfully. Apply result: **21 added, 0 changed, 0 destroyed**. Post-apply refresh result: **No changes; infrastructure matches the configuration**.

No secret versions or service-account keys were created. No secret values, access tokens, credential files, or Application Default Credential contents were read or printed. During this infrastructure apply, no GA4, advertising-platform, or Power BI Service work was performed; the later GA4 validation is recorded separately below.

## Apply and post-apply verification

The plan was regenerated as `terraform/tfplan` with the project, region, and bucket inputs. `terraform show tfplan` immediately confirmed **21 add, 0 change, 0 destroy**, after which `terraform apply tfplan` applied that saved artifact.

| Verification | Result |
|---|---|
| Terraform apply | PASS — 21 added, 0 changed, 0 destroyed |
| Terraform state | PASS — 21 expected resource addresses present |
| Post-apply drift check | PASS — exit 0; no changes |
| BigQuery datasets | PASS — `marketing_raw`, `marketing_staging`, `marketing_warehouse`, and `marketing_mart` live in `us-central1` |
| BigQuery dataset IAM | PASS — pipeline identity has writer/data-editor access on all four datasets |
| BigQuery dataset access smoke | PASS — authenticated metadata reads succeeded; no tables or destructive dataset tests were created |
| GCS bucket | PASS — live in `US-CENTRAL1`, public access prevention and uniform access enforced, versioning enabled |
| GCS bucket IAM | PASS — pipeline identity has bucket-scoped `roles/storage.objectAdmin` |
| GCS object smoke | PASS — one 29-byte object uploaded, read with exact expected contents, deleted, and confirmed absent from the live namespace |
| Pipeline service account | PASS — live and enabled; no user-managed keys exist |
| Project IAM | PASS — pipeline identity has `roles/bigquery.jobUser` |
| Secret containers | PASS — all three containers live with zero secret versions |
| Secret IAM | PASS — pipeline identity has `roles/secretmanager.secretAccessor` on each individual secret |
| Required APIs | PASS — BigQuery, Cloud Storage and Secret Manager enabled |

The bucket has the provider-default seven-day soft-delete policy (`604800` seconds). Consequently, the deleted 29-byte smoke object may remain as a soft-deleted/noncurrent object during retention even though it is absent from the live namespace. Its storage impact is negligible.

## LIVE VERIFIED — BigQuery data plane and dbt

Validated 2026-08-18 using 70 generated project rows. The GA4 export, advertising APIs, Secret Manager values, and vendor credentials were not used in this run.

### Adapter, routing, and cost controls

- dbt Core `1.11.11`; `dbt-bigquery` `1.9.2`; connection debug passed.
- Project/execution project: `p2-marketing-analytics-505916`.
- Location: `us-central1`.
- Source/raw: `marketing_raw`.
- Staging and intermediate: `marketing_staging`.
- Warehouse core: `marketing_warehouse`.
- Reporting mart: `marketing_mart`.
- Per-query `maximum_bytes_billed`: `104857600` bytes (100 MiB).

### Raw load — 70 total rows

Each table carries the operational labels `data_class=synthetic` and `validation=bounded_smoke` and inherits the raw dataset's 90-day default expiration.

| Raw table | Rows | Stored bytes |
|---|---:|---:|
| `campaign_mapping` | 10 | 1,053 |
| `facebook_ads` | 10 | 2,258 |
| `google_ads` | 10 | 2,019 |
| `region_mapping` | 10 | 566 |
| `sales_conversions` | 10 | 1,939 |
| `tiktok_ads` | 10 | 2,070 |
| `website_analytics` | 10 | 2,395 |

Raw total: **70 rows and 12,300 stored bytes**. The guarded loader refuses to overwrite an existing table unless it already carries both smoke labels.

### dbt execution — 40/40 passed

Command scope: `dbt build --select +mart_campaign_performance --threads 1`. It executed exactly 16 models and 24 attached tests; final result: **PASS=40, WARN=0, ERROR=0, SKIP=0**.

- Staging views: `stg_campaign_mapping`, `stg_facebook_ads`, `stg_google_ads`, `stg_region_mapping`, `stg_sales_conversions`, `stg_tiktok_ads`, `stg_website_analytics`.
- Intermediate views: `int_campaign_spend_unified`, `int_attribution_touchpoints`, `int_campaign_daily`.
- Warehouse tables: `dim_channel`, `dim_source_system`, `dim_region`, `dim_campaign`, `fact_campaign_performance`.
- Mart table: `mart_campaign_performance`.

The 24 tests covered accepted channel values, required keys/dates/spend, uniqueness, campaign SCD2 windows, and KPI relationships. All 24 passed; zero failed in the final run.

### Verified output row counts

| Layer | Relation | Type | Rows |
|---|---|---|---:|
| staging | `stg_campaign_mapping` | view | 10 |
| staging | `stg_facebook_ads` | view | 10 |
| staging | `stg_google_ads` | view | 10 |
| staging | `stg_region_mapping` | view | 10 |
| staging | `stg_sales_conversions` | view | 10 |
| staging | `stg_tiktok_ads` | view | 10 |
| staging | `stg_website_analytics` | view | 10 |
| intermediate | `int_campaign_spend_unified` | view | 30 |
| intermediate | `int_attribution_touchpoints` | view | 0 |
| intermediate | `int_campaign_daily` | view | 30 |
| warehouse | `dim_channel` | table | 7 |
| warehouse | `dim_source_system` | table | 7 |
| warehouse | `dim_region` | table | 15 |
| warehouse | `dim_campaign` | table | 32 |
| warehouse | `fact_campaign_performance` | incremental table | 30 |
| mart | `mart_campaign_performance` | table | 26 |

The attribution view contains zero rows because the independently sampled input identifiers do not intersect. Its SQL compiled and executed, while campaign transformations continued through the warehouse fact and mart.

### Bytes, errors, and estimated cost

- Final successful dbt run: 28,200 bytes processed; 471,859,200 bytes (450 MiB) billed after BigQuery minimum increments.
- Entire live BigQuery stage from 16:55 UTC, including raw loads, two diagnostic attempts, final run and verification: 7 load jobs, 76 query jobs, 33,869 bytes processed, 671,088,640 bytes (640 MiB) billed.
- Estimated charge before free-tier allowance: approximately `$0.004`; expected observed query charge is `$0` while within the billing account's first 1 TiB monthly on-demand allowance. Billing reports remain authoritative.

Two diagnostic attempts identified BigQuery incompatibilities before the successful run. The first exposed unsupported `text` casts and `VALUES` syntax; the second exposed parameterized `NUMERIC(p,s)` casts in expressions. Adapter-aware string, numeric, and date macros plus portable static dimensions fixed the issues. The same 40-node selector subsequently passed on DuckDB.

### Cleanup decision

No automatic cleanup was performed because these relations use stable project model names rather than disposable `tmp_*` names. Raw tables expire after 90 days by dataset policy; transformed tables and views remain until explicitly removed or rebuilt.

If cleanup is later requested, it would remove exactly the seven raw tables, ten staging/intermediate views, five warehouse tables, and one mart table listed above. It would not delete datasets, Terraform infrastructure, IAM, secrets, or unrelated relations. Review a cleanup plan before any deletion.

## LIVE VERIFIED — GA4 Daily export and dbt integration (updated 2026-08-20)

The Northstar Lab project site sends GA4 ecommerce events to property `550433518`. The Daily link exports to `p2-marketing-analytics-505916.analytics_550433518` in `us-central1`; Streaming export, user-data export, and advertising identifiers are off. Validation used Application Default Credentials and did not modify the raw GA4 dataset.

Verified architecture:

`Vercel live site` → `GA4 gtag.js` → `GA4 ecommerce events` → `GA4 Daily BigQuery export` → `analytics_550433518.events_*` → `dbt staging` → `live sessions/funnel` → `marketing_mart` → `Power BI / analytics-ready outputs`

### Source and date-filtered scan

- Accessible export tables: `analytics_550433518.events_20260818` and `analytics_550433518.events_20260819`.
- The second Daily table contains 3 rows and 3,182 logical bytes in `us-central1`; its exact live-host `view_item` query had a dry-run estimate of 897 bytes.
- dbt source: wildcard `events_*`, constrained by `_TABLE_SUFFIX` to a configurable 14-day lookback.
- Curated hostname: `p2.darshilmangukiya.com`; `127.0.0.1` and `localhost` are excluded in transformations, never deleted from raw.
- Event and repeated-item grains are modeled separately, preventing item unnesting from multiplying event totals.
- Per-query BigQuery guard remains 100 MiB.

### Live curated relations

| Dataset | Relation | Type | Rows | Grain |
|---|---|---|---:|---|
| `marketing_staging` | `stg_ga4_live_events` | view | 39 | one exported live-host event |
| `marketing_staging` | `stg_ga4_live_ecommerce_items` | view | 10 | one repeated ecommerce item |
| `marketing_staging` | `int_ga4_live_sessions` | view | 9 | one hashed user/session key |
| `marketing_mart` | `mart_ga4_live_funnel` | table | 2 | date/acquisition/device funnel aggregate |

Across both Daily tables, the live-domain export contains `add_to_cart` (3), `begin_checkout` (1), `first_visit` (7), `page_view` (8), `purchase` (1), `scroll` (5), `session_start` (9), `user_engagement` (4), and `view_item` (1), for 39 total curated events. The raw table's localhost events were excluded: **0 localhost rows** remain in curated event output.

The 10 parsed item rows cover three items at each of `add_to_cart`, `begin_checkout`, and `purchase`, plus one `view_item`: `signal-starter` / `Signal Starter`, category `Foundation`, USD `24`, quantity `1`. The event parameter value and repeated item price agree. Purchase transaction ID extraction passed its presence/uniqueness checks; transaction ID is retained only on purchase events. No secret or unnecessary raw pseudonymous identifier is exposed in the reporting mart.

Sessionization produced 9 sessions for 7 users: 5 engaged sessions, 8 page views, 1 view-item session, 1 add-to-cart session, 1 checkout session and 1 purchase session. The `2026-08-19` direct cohort contains 1 session/user and 1 view-item session/user: view-to-cart rate `0.0`, view-to-cart drop-off `1.0`, overall purchase-session rate `0.0`, and view-to-purchase rate `0.0`. The `2026-08-18` direct cohort retains cart-to-checkout `1.0`, checkout-to-purchase `1.0`, overall purchase-session rate `0.125`, 1 transaction and demo purchase value `124`; its view-based rates remain `null` because that cohort contains no view-item event. The stages occurred in separate dated sessions, so they must not be presented as one continuous journey. These tiny metrics validate pipeline behavior; they are not business-performance or causal conclusions.

### Tests and query cost

`dbt build --target bigquery --select tag:ga4_live` passed **34/34** operations: four models and 30 data tests, with zero warnings, errors or skips. Tests cover source readiness, required event fields, valid hostname/local exclusion, ecommerce event/value quality, purchase transaction integrity, session integrity, adjacent-stage timestamp ordering and funnel-rate bounds.

- Initial and final dbt build jobs: 647,499 bytes processed; 597,688,320 bytes billed (570 MiB).
- Three named validation queries: 40,521 bytes processed; 41,943,040 bytes billed (40 MiB).
- Combined observed scope: **688,020 bytes processed; 639,631,360 bytes billed (610 MiB)**.

The 2026-08-20 follow-up used 37 query jobs: the refreshed 34-job dbt build processed 352,617 bytes and billed 304,087,040 bytes (290 MiB); three named validation queries processed 19,498 bytes and billed 41,943,040 bytes (40 MiB). Follow-up total: **372,115 bytes processed and 346,030,080 bytes billed (330 MiB)**. Across both GA4 validation runs, **1,060,135 bytes were processed and 985,661,440 bytes were billed (940 MiB)**.

No monetary charge was observed; the workload was small and remains subject to the billing account's usage and free-tier status.

### Completion

GA4 Realtime includes `view_item`, `add_to_cart`, `begin_checkout`, `purchase`, `page_view`, and `session_start` from the deployed domain. `events_20260819` separately confirms the live-domain `view_item` and its item array in BigQuery. The exported page, session, engagement, cart, checkout, and purchase events complete the **LIVE GA4 → BIGQUERY → DBT** path. Vendor advertising APIs and Power BI Service remain separate stages.

## Terraform validation

The first `terraform fmt -check`, `init`, `validate`, and `plan` attempt exposed invalid single-line nested blocks in `main.tf`. The HCL was corrected without changing resource intent and formatted with Terraform. The final ordered validation results were:

| Command | Result | Output |
|---|---|---|
| `terraform fmt -check` | PASS | Exit 0; no formatting drift |
| `terraform init -input=false` | PASS | Google provider `6.50.0` installed and `.terraform.lock.hcl` generated |
| `terraform validate` | PASS | `Success! The configuration is valid.` |
| `terraform plan ...` | PASS | `21 to add, 0 to change, 0 to destroy` |

Plan inputs were supplied on the command line and were not persisted to a variable file:

- `project_id=p2-marketing-analytics-505916`
- `region=us-central1`
- proposed `gcs_bucket_name=p2-marketing-analytics-505916-data-lake`
- default environment `cloud-dev`

The pre-apply review plan was written to temporary storage at `/tmp/p2-live-validation.tfplan`. After approval, a fresh saved plan at `terraform/tfplan` was inspected and applied. Plan files and local state are ignored by Git.

## Exact provisioned resources

### APIs managed by Terraform — 3

1. `google_project_service.required["bigquery.googleapis.com"]`
2. `google_project_service.required["storage.googleapis.com"]`
3. `google_project_service.required["secretmanager.googleapis.com"]`

All three services were already enabled manually and are now tracked in Terraform state. `disable_on_destroy=false` prevents a future destroy from disabling them.

### BigQuery — 8

Four live datasets, all in `us-central1`, with no tables created by this infrastructure apply:

1. `google_bigquery_dataset.marketing["raw"]` → `marketing_raw`; default table expiration 7,776,000,000 ms (90 days)
2. `google_bigquery_dataset.marketing["staging"]` → `marketing_staging`
3. `google_bigquery_dataset.marketing["warehouse"]` → `marketing_warehouse`
4. `google_bigquery_dataset.marketing["mart"]` → `marketing_mart`

Four dataset-level grants give the pipeline identity `roles/bigquery.dataEditor`, one per dataset:

5. `google_bigquery_dataset_iam_member.pipeline_editor["raw"]`
6. `google_bigquery_dataset_iam_member.pipeline_editor["staging"]`
7. `google_bigquery_dataset_iam_member.pipeline_editor["warehouse"]`
8. `google_bigquery_dataset_iam_member.pipeline_editor["mart"]`

`delete_contents_on_destroy=false` is set on every dataset.

### Cloud Storage — 2

1. `google_storage_bucket.marketing_data_lake` → `p2-marketing-analytics-505916-data-lake`, location `US-CENTRAL1`, Standard storage, uniform bucket-level access, public access prevention enforced, versioning enabled, and `force_destroy=false`. Objects transition to Nearline after 30 days; older versions are deleted after 90 days when a newer version exists.
2. `google_storage_bucket_iam_member.pipeline_object_admin` → bucket-scoped `roles/storage.objectAdmin` for the pipeline identity.

### Secret Manager — 6

Live empty secret containers with automatic replication; Terraform created no secret versions or values:

1. `google_secret_manager_secret.vendor_credentials["google-ads"]` → `p2-google-ads-credentials`
2. `google_secret_manager_secret.vendor_credentials["meta-ads"]` → `p2-meta-ads-credentials`
3. `google_secret_manager_secret.vendor_credentials["tiktok-ads"]` → `p2-tiktok-ads-credentials`
4. `google_secret_manager_secret_iam_member.pipeline_accessor["google-ads"]`
5. `google_secret_manager_secret_iam_member.pipeline_accessor["meta-ads"]`
6. `google_secret_manager_secret_iam_member.pipeline_accessor["tiktok-ads"]`

Each IAM member grants the pipeline identity `roles/secretmanager.secretAccessor` only on its corresponding secret. Secret deletion protection is not enabled.

### Service account and project IAM — 2

1. `google_service_account.pipeline` → `p2-marketing-pipeline@p2-marketing-analytics-505916.iam.gserviceaccount.com`; no service-account key is created.
2. `google_project_iam_member.bigquery_job_user` → project-level `roles/bigquery.jobUser` for that service account.

Total: 3 API + 8 BigQuery + 2 Storage + 6 Secret Manager + 2 service-account/project-IAM resources = **21 added, 0 changed, 0 destroyed**.

## Read-only live connectivity and conflict checks

| Check | Result |
|---|---|
| GCP project access | PASS — project exists and lifecycle state is `ACTIVE` |
| BigQuery API | PASS — service enabled and dataset listing returned successfully |
| Cloud Storage API | PASS — service enabled and bucket listing returned successfully |
| Secret Manager API | PASS — service enabled and secret metadata listing returned successfully |
| Planned BigQuery dataset names | No existing datasets returned in the project |
| Proposed GCS bucket | Exact-name lookup returned `404 not found` |
| Planned secret names | No existing secrets returned |
| Planned pipeline service account | No existing service account returned |

No hard existing-resource conflicts occurred. Terraform currently uses local state; losing it could make later plans attempt to recreate globally unique or already-existing resources. The state is present, ignored by Git, refreshed successfully, and must be preserved securely. A remote backend is a future hardening option.

## Configuration, location, security, and cost review

- Project and requested region match exactly: `p2-marketing-analytics-505916` and `us-central1`.
- Repository defaults also match `us-central1` and the four planned dataset IDs. `.env.example` and `terraform.tfvars.example` intentionally keep project/bucket identifiers blank or placeholder-valued; the successful plan used the verified live identifiers as command-line variables. Before apply, use an ignored `terraform/terraform.tfvars` or the same explicit variables—never apply the placeholder example.
- BigQuery and GCS are co-located in `us-central1`, avoiding cross-region transfer between those resources.
- Secret Manager uses automatic replication, so it is Google-managed rather than explicitly pinned to `us-central1`; this is the only location nuance, not a project mismatch.
- IAM is scoped by dataset, bucket, or secret except for the required project-level BigQuery job-user role. `dataEditor` and `objectAdmin` can modify or delete data within their scopes, so the identity must remain pipeline-only.
- Public bucket access is prevented, uniform access is enabled, and no downloadable service-account key is created.
- Secret deletion protection is off. Empty containers are safe to create, but deletion protection should be reconsidered before storing irreplaceable production credentials.
- GCS versioning and provider-default soft-delete behavior can retain deleted data and add storage cost. The lifecycle policy reduces, but does not eliminate, that risk.
- No BigQuery reservation, VM, Kubernetes cluster, Composer environment, load balancer, static IP, or other always-on compute was created.

Expected baseline cost is approximately **$0/month and likely under $1/month**, provided usage remains within the billing account's available free tiers and queries stay small. Current official pricing indicates the first 1 TiB of BigQuery on-demand query processing per month is free, Cloud Storage provides 5 GB-months of Standard storage free in eligible regions including `us-central1`, and Secret Manager includes six active versions plus 10,000 access operations per month. Beyond those limits, usage is billable. See:

- <https://cloud.google.com/bigquery/pricing>
- <https://cloud.google.com/storage/pricing>
- <https://cloud.google.com/secret-manager/pricing>

No unexpected billable resource was created. Overall operating risk remains **low but non-zero**: the infrastructure establishes write-capable IAM, billable storage/query surfaces, a seven-day GCS soft-delete policy, and relies on local Terraform state. Budget alerts are configured.
