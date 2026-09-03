from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from connectors.auth import OAuth2RefreshClient, OAuthError, OAuthToken
from connectors.base import ConnectorError
from connectors.google_ads import GoogleAdsConnector
from connectors.meta_ads import MetaAdsConnector
from connectors.models import ExtractionWindow
from connectors.retry import RetryPolicy
from connectors.tiktok_ads import TikTokAdsConnector


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200, headers: dict | None = None) -> None:
        self.payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self) -> dict:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def window() -> ExtractionWindow:
    return ExtractionWindow(date(2025, 1, 1), date(2025, 1, 31), watermark="2024-12-31")


def test_google_ads_paginates_retries_and_normalizes_micros() -> None:
    session = FakeSession(
        [
            FakeResponse({}, 429, {"Retry-After": "0"}),
            FakeResponse(
                {
                    "results": [{"campaign": {"id": 1, "name": "Brand"}, "adGroup": {"id": 2}, "segments": {"date": "2025-01-05"}, "metrics": {"impressions": "100", "clicks": "10", "costMicros": "2500000", "conversions": "2", "conversionsValue": "25"}}],
                    "nextPageToken": "next",
                },
                headers={"request-id": "r1", "x-ratelimit-remaining": "10"},
            ),
            FakeResponse({"results": []}, headers={"request-id": "r2"}),
        ]
    )
    connector = GoogleAdsConnector(
        "https://fixture.invalid",
        "sensitive-access-token",
        customer_id="123-456",
        developer_token="sensitive-developer-token",
        session=session,
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0),
        sleeper=lambda _: None,
    )
    result = connector.extract(window(), page_size=10)
    assert result.page_count == 2
    assert result.retry_count == 1
    assert result.records[0]["spend"] == 2.5
    assert result.last_watermark == "2025-01-05"
    assert session.calls[-1][1]["params"]["page_token"] == "next"
    assert "developer_token" not in session.calls[-1][1]["params"]
    assert session.calls[-1][1]["headers"]["developer-token"] == "sensitive-developer-token"


def test_empty_meta_response_is_valid() -> None:
    connector = MetaAdsConnector("https://fixture.invalid", "token", account_id="act_1", session=FakeSession([FakeResponse({"data": []})]))
    result = connector.extract(window())
    assert result.records == []
    assert result.page_count == 1


def test_tiktok_pagination_and_schema_normalization() -> None:
    session = FakeSession(
        [
            FakeResponse({"code": 0, "data": {"list": [{"dimensions": {"campaign_id": "9", "stat_time_day": "2025-01-01"}, "metrics": {"spend": "4.5", "clicks": "3"}}], "page_info": {"page": 1, "total_page": 2}}}),
            FakeResponse({"code": 0, "data": {"list": [], "page_info": {"page": 2, "total_page": 2}}}),
        ]
    )
    result = TikTokAdsConnector("https://fixture.invalid", "token", advertiser_id="adv_1", session=session).extract(window())
    assert result.page_count == 2
    assert result.records[0]["spend"] == 4.5


def test_malformed_vendor_response_is_classified_without_token_leak() -> None:
    connector = MetaAdsConnector(
        "https://fixture.invalid",
        "do-not-leak",
        account_id="act_1",
        session=FakeSession([FakeResponse({"data": "wrong"})]),
        retry_policy=RetryPolicy(max_attempts=1),
    )
    with pytest.raises(ConnectorError) as error:
        connector.extract(window())
    assert "do-not-leak" not in str(error.value)


def test_exhausted_rate_limit_is_clear_and_redacted() -> None:
    connector = MetaAdsConnector(
        "https://fixture.invalid",
        "do-not-leak",
        account_id="act_1",
        session=FakeSession([FakeResponse({}, 429), FakeResponse({}, 429)]),
        retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0),
        sleeper=lambda _: None,
    )
    with pytest.raises(ConnectorError, match="exhausted retries") as error:
        connector.extract(window())
    assert "do-not-leak" not in str(error.value)


def test_extraction_window_rejects_reverse_dates() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        ExtractionWindow(date(2025, 2, 1), date(2025, 1, 1))


def test_oauth_refresh_and_expiry_without_logging_secrets() -> None:
    class OAuthSession:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            assert kwargs["data"]["client_secret"] == "client-secret"
            return FakeResponse({"access_token": "new-token", "expires_in": 3600})

    expired = OAuthToken("old-token", "refresh-token", datetime.now(timezone.utc) - timedelta(seconds=1))
    assert expired.is_expiring()
    refreshed = OAuth2RefreshClient("https://oauth.invalid/token", "client", "client-secret", OAuthSession()).refresh(expired)
    assert refreshed.access_token == "new-token"
    assert refreshed.refresh_token == "refresh-token"


def test_oauth_failure_message_is_redacted() -> None:
    class BrokenSession:
        def post(self, url: str, **kwargs: object) -> FakeResponse:
            return FakeResponse({"error": "includes-sensitive-token"}, 400)

    with pytest.raises(OAuthError) as error:
        OAuth2RefreshClient("https://oauth.invalid/token", "client", "secret", BrokenSession()).refresh(OAuthToken("access", "refresh"))
    assert "sensitive" not in str(error.value)
