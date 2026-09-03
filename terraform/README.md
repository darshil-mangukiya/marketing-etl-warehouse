# GCP Terraform

This opt-in scaffold provisions a small GCS bucket, four on-demand BigQuery datasets, Secret Manager containers, and a keyless least-privilege pipeline service account. It does not create a GCP project, attach billing, upload secrets, create service-account keys, reserve BigQuery slots, or deploy always-on compute.

The configuration was applied with Terraform 1.15.8 and Google provider 6.50.0 on 2026-08-18 after a saved plan was reviewed at 21 add, 0 change and 0 destroy. Live verification covered four BigQuery datasets, the private GCS bucket, the keyless service account, scoped IAM, three empty secret containers and required APIs. A post-apply plan reported no drift. No secret versions or service-account keys were created.

For a future reviewed change, copy `terraform.tfvars.example` to an ignored `terraform.tfvars`, authenticate with Application Default Credentials, then run `terraform init`, `terraform fmt -check`, `terraform validate`, and `terraform plan`. Review the plan and cost implications before any explicit apply. Never run `terraform destroy` against data you need to retain; both the bucket and datasets refuse content deletion by default. State remains local and ignored, so it must be preserved securely. The Python/local path does not depend on Terraform.
