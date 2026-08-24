# Cloud Cost Safety

The live Terraform foundation contains one small GCS bucket, four on-demand BigQuery datasets, three empty Secret Manager containers, one keyless service account, and scoped IAM and API-management resources. The apply created 21 resources with no changes or destroys, and the post-apply plan reported no drift. It does not deploy VMs, Kubernetes, managed Airflow, BigQuery reservations, or always-on compute.

Likely cost drivers are BigQuery bytes scanned and stored, GCS storage, operations and egress, retained object versions, Secret Manager access, and accidental large scale-profile runs. Keep the local smoke profile as default, use one region, preview query bytes, select required columns, set budgets and alerts, expire disposable raw tables, and remove unused object versions.

Before any future Terraform change, review `terraform plan`, confirm the existing budget alert and target project, and retain `force_destroy=false` and `delete_contents_on_destroy=false`. To shut down, disable schedules and API jobs first, export anything needed, delete objects/tables deliberately, then remove empty resources. Never use an unreviewed destroy command.

For the current smoke workload, expected baseline cost is approximately $0/month and likely under $1/month if the billing account's available free tiers are not already consumed. The principal risks are BigQuery bytes scanned, stored data, retained GCS versions or soft-deleted objects, operations and egress, and Secret Manager versions or access above free allowances. Current pricing references: <https://cloud.google.com/bigquery/pricing>, <https://cloud.google.com/storage/pricing>, and <https://cloud.google.com/secret-manager/pricing>.

The current Terraform backend is local. Preserve the state securely after any apply; losing it creates drift and duplicate-resource risk. Do not commit state, plan files, local variable files, or the `.terraform/` directory.
