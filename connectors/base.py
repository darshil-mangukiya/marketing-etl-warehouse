from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone

import requests

from cloud_platform.storage import StorageBackend
from connectors.models import ExtractionResult, ExtractionWindow, PageResult
from connectors.retry import RetryPolicy, sleep_with_policy


class ConnectorError(RuntimeError):
    pass


class BaseMarketingConnector(ABC):
    source_system: str
    endpoint: str

    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        session: object | None = None,
        retry_policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if not access_token:
            raise ValueError(f"{self.source_system} access token is required for live extraction.")
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self.session = session or requests.Session()
        self.retry_policy = retry_policy or RetryPolicy()
        self.sleeper = sleeper or time.sleep

    def extract(self, window: ExtractionWindow, page_size: int = 500) -> ExtractionResult:
        result = ExtractionResult(source_system=self.source_system, last_watermark=window.watermark)
        page_token = None
        while True:
            page, retries = self._fetch_page(window, page_token, page_size)
            result.retry_count += retries
            result.page_count += 1
            result.records.extend(self.normalize(record) for record in page.records)
            result.response_metadata.append(
                {
                    "page": result.page_count,
                    "request_id": page.request_id,
                    "row_count": len(page.records),
                    "rate_limit_remaining": page.rate_limit_remaining,
                }
            )
            page_token = page.next_page_token
            if not page_token:
                break
        result.last_watermark = max(
            (str(record.get("event_date")) for record in result.records if record.get("event_date")),
            default=window.watermark,
        )
        return result

    def extract_and_land(self, window: ExtractionWindow, storage: StorageBackend, batch_id: str) -> tuple[ExtractionResult, str]:
        result = self.extract(window)
        payload = "\n".join(json.dumps(record, sort_keys=True, default=str) for record in result.records).encode("utf-8")
        object_name = f"raw/{self.source_system}/batch_id={batch_id}/{self.source_system}.jsonl"
        stored = storage.put_bytes(object_name, payload, batch_id=batch_id, source_system=self.source_system)
        return result, stored.uri

    def _fetch_page(self, window: ExtractionWindow, page_token: str | None, page_size: int) -> tuple[PageResult, int]:
        retries = 0
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                response = self.session.get(
                    f"{self.base_url}/{self.endpoint.lstrip('/')}",
                    headers=self.request_headers(),
                    params=self.request_params(window, page_token, page_size),
                    timeout=30,
                )
                if response.status_code in self.retry_policy.retry_statuses:
                    if attempt == self.retry_policy.max_attempts:
                        raise ConnectorError(f"{self.source_system} request exhausted retries with HTTP {response.status_code}.")
                    retries += 1
                    sleep_with_policy(self.retry_policy, attempt, response.headers.get("Retry-After"), self.sleeper)
                    continue
                response.raise_for_status()
                return self.parse_page(response.json(), dict(response.headers)), retries
            except ConnectorError:
                raise
            except Exception as exc:
                if attempt == self.retry_policy.max_attempts:
                    raise ConnectorError(f"{self.source_system} request failed after {attempt} attempts; credentials and response body were redacted.") from exc
                retries += 1
                sleep_with_policy(self.retry_policy, attempt, None, self.sleeper)
        raise ConnectorError(f"{self.source_system} request failed unexpectedly.")

    def request_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    @abstractmethod
    def request_params(self, window: ExtractionWindow, page_token: str | None, page_size: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def parse_page(self, payload: dict, headers: dict[str, str]) -> PageResult:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, record: dict) -> dict:
        raise NotImplementedError

    @staticmethod
    def metadata(source_system: str) -> dict:
        return {"source_system": source_system, "extracted_at": datetime.now(timezone.utc).isoformat()}
