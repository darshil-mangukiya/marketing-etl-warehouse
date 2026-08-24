from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class StoredObject:
    uri: str
    size_bytes: int
    sha256: str
    batch_id: str
    source_system: str
    ingestion_timestamp: str


class StorageBackend(ABC):
    @abstractmethod
    def put_bytes(self, object_name: str, payload: bytes, *, batch_id: str, source_system: str) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def exists(self, object_name: str) -> bool:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def put_bytes(self, object_name: str, payload: bytes, *, batch_id: str, source_system: str) -> StoredObject:
        target = (self.root / object_name).resolve()
        if self.root != target and self.root not in target.parents:
            raise ValueError(f"Storage object escapes configured root: {object_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        record = StoredObject(
            uri=str(target),
            size_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            batch_id=batch_id,
            source_system=source_system,
            ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        target.with_suffix(target.suffix + ".metadata.json").write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
        return record

    def exists(self, object_name: str) -> bool:
        return (self.root / object_name).exists()


class GCSStorageBackend(StorageBackend):
    def __init__(self, bucket_name: str, client: object | None = None) -> None:
        if not bucket_name:
            raise ValueError("GCS bucket name cannot be empty.")
        if client is None:
            try:
                from google.cloud import storage
            except ImportError as exc:
                raise RuntimeError("GCS support requires `pip install -r requirements-cloud.txt`.") from exc
            client = storage.Client()
        self.bucket_name = bucket_name
        self.client = client

    def put_bytes(self, object_name: str, payload: bytes, *, batch_id: str, source_system: str) -> StoredObject:
        digest = hashlib.sha256(payload).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        blob.metadata = {
            "batch_id": batch_id,
            "source_system": source_system,
            "sha256": digest,
            "ingestion_timestamp": timestamp,
        }
        blob.upload_from_string(payload)
        return StoredObject(
            uri=f"gs://{self.bucket_name}/{object_name}",
            size_bytes=len(payload),
            sha256=digest,
            batch_id=batch_id,
            source_system=source_system,
            ingestion_timestamp=timestamp,
        )

    def exists(self, object_name: str) -> bool:
        return bool(self.client.bucket(self.bucket_name).blob(object_name).exists())
