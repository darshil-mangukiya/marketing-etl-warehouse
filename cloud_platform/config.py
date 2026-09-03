from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    LOCAL = "local"
    TEST = "test"
    CLOUD = "cloud"


class CloudConfigurationError(ValueError):
    """Raised when cloud mode is selected without its required configuration."""


@dataclass(frozen=True)
class CloudConfig:
    mode: ExecutionMode = ExecutionMode.LOCAL
    project_id: str | None = None
    region: str = "us-central1"
    gcs_bucket: str | None = None
    raw_dataset: str = "marketing_raw"
    staging_dataset: str = "marketing_staging"
    warehouse_dataset: str = "marketing_warehouse"
    mart_dataset: str = "marketing_mart"
    secret_provider: str = "environment"

    @classmethod
    def from_env(cls) -> CloudConfig:
        raw_mode = os.getenv("EXECUTION_MODE", os.getenv("ENVIRONMENT", "local")).lower()
        mode = ExecutionMode.CLOUD if raw_mode in {"cloud", "cloud-dev", "prod"} else ExecutionMode(raw_mode if raw_mode in {"local", "test"} else "local")
        config = cls(
            mode=mode,
            project_id=os.getenv("GCP_PROJECT_ID") or None,
            region=os.getenv("GCP_REGION", "us-central1"),
            gcs_bucket=os.getenv("GCS_BUCKET") or None,
            raw_dataset=os.getenv("BIGQUERY_RAW_DATASET", "marketing_raw"),
            staging_dataset=os.getenv("BIGQUERY_STAGING_DATASET", "marketing_staging"),
            warehouse_dataset=os.getenv("BIGQUERY_WAREHOUSE_DATASET", "marketing_warehouse"),
            mart_dataset=os.getenv("BIGQUERY_MART_DATASET", "marketing_mart"),
            secret_provider=os.getenv("SECRET_PROVIDER", "environment"),
        )
        if config.mode is ExecutionMode.CLOUD:
            config.validate_cloud()
        return config

    @property
    def is_cloud(self) -> bool:
        return self.mode is ExecutionMode.CLOUD

    def validate_cloud(self, require_bucket: bool = True) -> None:
        missing = []
        if not self.project_id:
            missing.append("GCP_PROJECT_ID")
        if require_bucket and not self.gcs_bucket:
            missing.append("GCS_BUCKET")
        if missing:
            raise CloudConfigurationError(
                "Cloud mode is missing required configuration: " + ", ".join(missing) + ". Copy .env.example and set only non-secret identifiers there; use environment variables or Secret Manager for credentials."
            )

    def dataset_ids(self) -> tuple[str, ...]:
        if not self.project_id:
            raise CloudConfigurationError("GCP_PROJECT_ID is required to resolve BigQuery datasets.")
        return tuple(
            f"{self.project_id}.{dataset}"
            for dataset in (self.raw_dataset, self.staging_dataset, self.warehouse_dataset, self.mart_dataset)
        )
