locals {
  datasets = {
    raw       = var.bigquery_raw_dataset
    staging   = var.bigquery_staging_dataset
    warehouse = var.bigquery_warehouse_dataset
    mart      = var.bigquery_mart_dataset
  }
  required_services = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "marketing_data_lake" {
  name                        = var.gcs_bucket_name
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age                = 90
      num_newer_versions = 1
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_bigquery_dataset" "marketing" {
  for_each                    = local.datasets
  project                     = var.project_id
  dataset_id                  = each.value
  friendly_name               = "P2 marketing ${each.key}"
  description                 = "P2 marketing ${each.key} dataset; generated data is the default source."
  location                    = var.region
  delete_contents_on_destroy  = false
  default_table_expiration_ms = each.key == "raw" ? var.raw_table_expiration_ms : null

  labels = {
    environment = var.environment
    project     = "p2-marketing"
    layer       = each.key
  }

  depends_on = [google_project_service.required]
}

resource "google_service_account" "pipeline" {
  project      = var.project_id
  account_id   = "p2-marketing-pipeline"
  display_name = "P2 Marketing Pipeline"
  description  = "Least-privilege P2 pipeline identity; Terraform does not create a key."
}

resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "pipeline_editor" {
  for_each   = google_bigquery_dataset.marketing
  project    = var.project_id
  dataset_id = each.value.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "pipeline_object_admin" {
  bucket = google_storage_bucket.marketing_data_lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_secret_manager_secret" "vendor_credentials" {
  for_each  = toset(["google-ads", "meta-ads", "tiktok-ads"])
  project   = var.project_id
  secret_id = "p2-${each.value}-credentials"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "pipeline_accessor" {
  for_each  = google_secret_manager_secret.vendor_credentials
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pipeline.email}"
}
