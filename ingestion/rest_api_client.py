from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.file_io import write_frame


@dataclass(frozen=True)
class ExtractedApiPage:
    source_system: str
    page_number: int
    row_count: int
    next_page_token: str | None
    output_path: Path


class MarketingApiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def iter_records(
        self,
        source_system: str,
        page_size: int = 1000,
        updated_after: str | None = None,
        failure_rate: float = 0.0,
    ) -> Iterator[pd.DataFrame]:
        page_token: str | None = None
        while True:
            payload = self._get_json(
                f"/v1/{source_system}/records",
                params={
                    "page_size": page_size,
                    "page_token": page_token,
                    "updated_after": updated_after,
                    "failure_rate": failure_rate,
                },
            )
            records = payload["records"]
            if records:
                yield pd.DataFrame(records)
            page_token = payload.get("next_page_token")
            if not page_token:
                break

    def _get_json(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout_seconds)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise requests.HTTPError(f"{response.status_code}: {response.text}", response=response)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.backoff_seconds * attempt)
        raise RuntimeError(f"API request failed after {self.max_retries} attempts: {last_error}") from last_error


def extract_mock_api_sources(
    base_url: str = "http://localhost:8000",
    token: str = "local-dev-token",
    sources: list[str] | None = None,
    page_size: int = 1000,
    updated_after: str | None = None,
    output_format: str = "jsonl",
) -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    sources = sources or ["google_ads", "facebook_ads", "tiktok_ads"]
    client = MarketingApiClient(base_url=base_url, token=token)
    batch_id = f"api_batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = {
        "batch_id": batch_id,
        "base_url": base_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parts": [],
    }
    for source_system in sources:
        for page_number, frame in enumerate(
            client.iter_records(source_system, page_size=page_size, updated_after=updated_after),
            start=1,
        ):
            output_path = (
                config.project_root
                / "data_sources"
                / "api_extracted"
                / f"source_system={source_system}"
                / f"batch_id={batch_id}"
                / f"{source_system}_api_page_{page_number:05d}.{output_format}"
            )
            written_path, actual_format = write_frame(frame, output_path, output_format)
            manifest["parts"].append(
                {
                    "source_system": source_system,
                    "path": str(written_path.relative_to(config.project_root)),
                    "row_count": len(frame),
                    "file_format": actual_format,
                    "page_number": page_number,
                }
            )
    manifest_path = config.project_root / "data_sources" / "api_extracted" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract paginated records from the local FastAPI source simulator.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", default="local-dev-token")
    parser.add_argument("--sources", nargs="*", default=["google_ads", "facebook_ads", "tiktok_ads"])
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--updated-after", default=None)
    parser.add_argument("--format", default="jsonl", choices=["jsonl", "csv", "parquet"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = extract_mock_api_sources(
        base_url=args.base_url,
        token=args.token,
        sources=args.sources,
        page_size=args.page_size,
        updated_after=args.updated_after,
        output_format=args.format,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
