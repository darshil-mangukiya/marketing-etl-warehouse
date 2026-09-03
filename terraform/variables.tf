variable "project_id" {
  type        = string
  description = "Existing GCP project ID. Terraform does not create or attach billing accounts."
}

variable "region" {
  type        = string
  description = "GCP location shared by GCS and BigQuery to avoid cross-region transfer."
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Deployment environment label."
  default     = "cloud-dev"
}

variable "gcs_bucket_name" {
  type        = string
  description = "Globally unique GCS bucket name."
}

variable "bigquery_raw_dataset" {
  type    = string
  default = "marketing_raw"
}

variable "bigquery_staging_dataset" {
  type    = string
  default = "marketing_staging"
}

variable "bigquery_warehouse_dataset" {
  type    = string
  default = "marketing_warehouse"
}

variable "bigquery_mart_dataset" {
  type    = string
  default = "marketing_mart"
}

variable "raw_table_expiration_ms" {
  type        = number
  description = "Optional raw table retention in milliseconds; null disables automatic expiration."
  default     = 7776000000
}
