from __future__ import annotations

from pathlib import Path

import pytest

from cloud_platform.bigquery import BigQueryWarehouse
from cloud_platform.config import CloudConfig, CloudConfigurationError, ExecutionMode
from cloud_platform.secrets import (
    EnvironmentSecretProvider,
    GoogleSecretManagerProvider,
    SecretNotFoundError,
)
from cloud_platform.storage import GCSStorageBackend, LocalStorageBackend


class FakeBlob:
    def __init__(self, name: str) -> None:
        self.name = name
        self.metadata = None
        self.payload = None

    def upload_from_string(self, payload: bytes) -> None:
        self.payload = payload

    def exists(self) -> bool:
        return self.payload is not None


class FakeBucket:
    def __init__(self) -> None:
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        return self.blobs.setdefault(name, FakeBlob(name))


class FakeStorageClient:
    def __init__(self) -> None:
        self.value = FakeBucket()

    def bucket(self, name: str) -> FakeBucket:
        assert name == "project-bucket"
        return self.value


class FakeJob:
    job_id = "fixture-job"
    output_rows = 1

    def result(self) -> FakeJob:
        return self


class FakeBigQueryClient:
    def __init__(self) -> None:
        self.datasets = []
        self.loaded = None

    def create_dataset(self, dataset: object, exists_ok: bool) -> None:
        assert exists_ok is True
        self.datasets.append(dataset)

    def load_table_from_json(self, rows: list[dict], table_id: str, job_config: object) -> FakeJob:
        self.loaded = (rows, table_id, job_config)
        return FakeJob()


def test_local_cloud_config_has_no_credential_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXECUTION_MODE", "local")
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    assert CloudConfig.from_env().mode is ExecutionMode.LOCAL


def test_cloud_config_names_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXECUTION_MODE", "cloud")
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCS_BUCKET", raising=False)
    with pytest.raises(CloudConfigurationError, match="GCP_PROJECT_ID, GCS_BUCKET"):
        CloudConfig.from_env()


def test_local_storage_writes_payload_and_metadata(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    stored = backend.put_bytes("raw/ga4/events.jsonl", b"{}\n", batch_id="b1", source_system="ga4")
    assert stored.sha256
    assert backend.exists("raw/ga4/events.jsonl")
    assert (tmp_path / "raw/ga4/events.jsonl.metadata.json").exists()


def test_local_storage_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        LocalStorageBackend(tmp_path).put_bytes("../outside", b"x", batch_id="b1", source_system="ga4")


def test_gcs_storage_preserves_operational_metadata() -> None:
    client = FakeStorageClient()
    backend = GCSStorageBackend("project-bucket", client=client)
    result = backend.put_bytes("raw/google_ads/page.json", b"[]", batch_id="b2", source_system="google_ads")
    blob = client.value.blob("raw/google_ads/page.json")
    assert result.uri == "gs://project-bucket/raw/google_ads/page.json"
    assert blob.metadata["batch_id"] == "b2"
    assert "sha256" in blob.metadata


def test_bigquery_helper_is_idempotent_and_restricts_datasets() -> None:
    config = CloudConfig(mode=ExecutionMode.CLOUD, project_id="project-id", gcs_bucket="bucket")
    client = FakeBigQueryClient()
    warehouse = BigQueryWarehouse(config, client=client)
    assert len(warehouse.ensure_datasets()) == 4
    result = warehouse.load_json_rows(config.raw_dataset, "google_ads", [{"campaign_id": "1"}])
    assert result.input_rows == 1
    assert result.job_id == "fixture-job"
    with pytest.raises(ValueError, match="not declared"):
        warehouse.load_json_rows("unknown", "table", [])


def test_environment_secret_provider_never_returns_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_TOKEN", raising=False)
    with pytest.raises(SecretNotFoundError, match="MISSING_TOKEN"):
        EnvironmentSecretProvider().get("MISSING_TOKEN")


def test_secret_manager_error_does_not_expose_secret_value() -> None:
    class BrokenClient:
        def access_secret_version(self, request: dict) -> None:
            raise RuntimeError("access denied")

    provider = GoogleSecretManagerProvider("project-id", client=BrokenClient())
    with pytest.raises(SecretNotFoundError, match="vendor-token") as error:
        provider.get("vendor-token")
    assert "access denied" not in str(error.value)
