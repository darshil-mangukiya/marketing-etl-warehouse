output "gcs_bucket" {
  value       = google_storage_bucket.marketing_data_lake.name
  description = "GCS data-lake bucket."
}

output "bigquery_datasets" {
  value       = { for layer, dataset in google_bigquery_dataset.marketing : layer => dataset.dataset_id }
  description = "BigQuery layer-to-dataset mapping."
}

output "pipeline_service_account" {
  value       = google_service_account.pipeline.email
  description = "Keyless pipeline identity."
}
