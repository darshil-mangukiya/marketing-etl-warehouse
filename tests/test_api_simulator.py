import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api_simulator import main as api_main
from api_simulator.pagination import parse_page_token

AUTH_HEADERS = {"Authorization": f"Bearer {api_main.DEFAULT_TOKEN}"}


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    source_path = tmp_path / "google_ads.csv"
    pd.DataFrame(
        [
            {"record_id": "row-1", "updated_at": "2026-08-20T00:00:00Z"},
            {"record_id": "row-2", "updated_at": "2026-08-21T00:00:00Z"},
            {"record_id": "row-3", "updated_at": "2026-08-22T00:00:00Z"},
        ]
    ).to_csv(source_path, index=False)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "parts": [
                    {"source_system": "google_ads", "path": str(source_path)},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SOURCE_MANIFEST_PATH", str(manifest_path))
    return TestClient(api_main.app)


def test_parse_empty_page_token_starts_at_first_file() -> None:
    assert parse_page_token(None) == (0, 0)


def test_parse_page_token_pair() -> None:
    assert parse_page_token("3:2500") == (3, 2500)


def test_parse_bad_page_token_raises_http_error() -> None:
    try:
        parse_page_token("bad-token")
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Expected HTTPException")


def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["manifest_exists"] is True


def test_sources_endpoint_lists_supported_sources(api_client: TestClient) -> None:
    response = api_client.get("/v1/sources", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["sources"] == ["facebook_ads", "google_ads", "tiktok_ads"]


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer invalid-token"}],
)
def test_sources_endpoint_rejects_missing_or_invalid_token(
    api_client: TestClient,
    headers: dict[str, str],
) -> None:
    response = api_client.get("/v1/sources", headers=headers)

    assert response.status_code == 401


def test_records_endpoint_paginates(api_client: TestClient) -> None:
    first = api_client.get(
        "/v1/google_ads/records?page_size=2",
        headers=AUTH_HEADERS,
    )
    second = api_client.get(
        f"/v1/google_ads/records?page_size=2&page_token={first.json()['next_page_token']}",
        headers=AUTH_HEADERS,
    )

    assert first.status_code == 200
    assert first.json()["record_count"] == 2
    assert first.json()["next_page_token"] == "0:2"
    assert second.status_code == 200
    assert second.json()["record_count"] == 1
    assert second.json()["next_page_token"] is None


def test_records_endpoint_rejects_invalid_source(api_client: TestClient) -> None:
    response = api_client.get("/v1/invalid/records", headers=AUTH_HEADERS)

    assert response.status_code == 404


@pytest.mark.parametrize("page_size", [0, 5001])
def test_records_endpoint_enforces_page_size_bounds(
    api_client: TestClient,
    page_size: int,
) -> None:
    response = api_client.get(
        f"/v1/google_ads/records?page_size={page_size}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_records_endpoint_filters_by_updated_after(api_client: TestClient) -> None:
    response = api_client.get(
        "/v1/google_ads/records?updated_after=2026-08-21T00:00:00Z",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["record_count"] == 1
    assert response.json()["records"][0]["record_id"] == "row-3"


def test_records_endpoint_simulates_upstream_failure(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api_main.random, "random", lambda: 0.0)

    response = api_client.get(
        "/v1/google_ads/records?failure_rate=0.5",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
