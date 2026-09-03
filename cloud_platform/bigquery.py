from __future__ import annotations

from dataclasses import dataclass

from cloud_platform.config import CloudConfig


@dataclass(frozen=True)
class BigQueryLoadResult:
    table_id: str
    input_rows: int
    output_rows: int | None
    job_id: str | None


class BigQueryWarehouse:
    def __init__(self, config: CloudConfig, client: object | None = None) -> None:
        config.validate_cloud(require_bucket=False)
        if client is None:
            try:
                from google.cloud import bigquery
            except ImportError as exc:
                raise RuntimeError("BigQuery support requires `pip install -r requirements-cloud.txt`.") from exc
            client = bigquery.Client(project=config.project_id, location=config.region)
        self.config = config
        self.client = client

    def ensure_datasets(self) -> list[str]:
        created_or_existing = []
        for dataset_id in self.config.dataset_ids():
            try:
                from google.cloud import bigquery

                dataset = bigquery.Dataset(dataset_id)
                dataset.location = self.config.region
            except ImportError:
                dataset = dataset_id
            self.client.create_dataset(dataset, exists_ok=True)
            created_or_existing.append(dataset_id)
        return created_or_existing

    def load_json_rows(self, dataset: str, table: str, rows: list[dict], *, write_disposition: str = "WRITE_APPEND") -> BigQueryLoadResult:
        if dataset not in {self.config.raw_dataset, self.config.staging_dataset, self.config.warehouse_dataset, self.config.mart_dataset}:
            raise ValueError(f"Dataset {dataset} is not declared in CloudConfig.")
        table_id = f"{self.config.project_id}.{dataset}.{table}"
        job_config = None
        try:
            from google.cloud import bigquery

            job_config = bigquery.LoadJobConfig(write_disposition=write_disposition)
        except ImportError:
            pass
        job = self.client.load_table_from_json(rows, table_id, job_config=job_config)
        result = job.result()
        return BigQueryLoadResult(
            table_id=table_id,
            input_rows=len(rows),
            output_rows=getattr(result, "output_rows", None),
            job_id=getattr(job, "job_id", None),
        )
