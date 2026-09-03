# Google Cloud Storage Integration

`cloud_platform.storage.StorageBackend` provides a common write/existence contract. `LocalStorageBackend` is the default and confines objects to its configured root. `GCSStorageBackend` is optional and is instantiated only after cloud dependencies and credentials are present.

Objects use paths such as `raw/google_ads/batch_id=<id>/google_ads.jsonl`, `raw/meta_ads/`, `raw/tiktok_ads/`, `raw/ga4/`, `processed/`, `rejected/` and `archive/`. Every landed object carries batch ID, source system, ingestion timestamp, SHA-256 and size. The local backend writes a sidecar metadata file; GCS uses custom object metadata.

Install `requirements-cloud.txt`, set `GCP_PROJECT_ID`, `GCP_REGION` and `GCS_BUCKET`, then authenticate with Application Default Credentials. The Terraform bucket enforces uniform access and public-access prevention, retains versions, refuses force deletion and transitions older objects to Nearline.

On 2026-08-18, Terraform provisioned `p2-marketing-analytics-505916-data-lake` in `us-central1` with uniform bucket-level access, public-access prevention, versioning, and `force_destroy=false`. Live IAM verification passed, and one tiny temporary object was written, read, and deleted successfully. No project dataset was modified.
