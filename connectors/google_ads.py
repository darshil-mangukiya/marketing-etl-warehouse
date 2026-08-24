from __future__ import annotations

from connectors.base import BaseMarketingConnector
from connectors.models import ExtractionWindow, PageResult


class GoogleAdsConnector(BaseMarketingConnector):
    source_system = "google_ads"
    endpoint = "googleAds:search"

    def __init__(self, base_url: str, access_token: str, customer_id: str, developer_token: str, **kwargs: object) -> None:
        super().__init__(base_url, access_token, **kwargs)
        self.customer_id = customer_id.replace("-", "")
        self.developer_token = developer_token

    def request_params(self, window: ExtractionWindow, page_token: str | None, page_size: int) -> dict:
        return {
            "customer_id": self.customer_id,
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
            "page_token": page_token,
            "page_size": page_size,
        }

    def request_headers(self) -> dict[str, str]:
        return {**super().request_headers(), "developer-token": self.developer_token}

    def parse_page(self, payload: dict, headers: dict[str, str]) -> PageResult:
        records = payload.get("results", [])
        if not isinstance(records, list):
            raise ValueError("Malformed Google Ads response: results must be a list.")
        return PageResult(records, payload.get("nextPageToken"), headers.get("request-id"), _integer(headers.get("x-ratelimit-remaining")))

    def normalize(self, record: dict) -> dict:
        campaign = record.get("campaign", {})
        metrics = record.get("metrics", {})
        segments = record.get("segments", {})
        micros = float(metrics.get("costMicros", 0) or 0)
        return {
            **self.metadata(self.source_system),
            "account_id": self.customer_id,
            "campaign_id": str(campaign.get("id", "")),
            "campaign_name": campaign.get("name"),
            "ad_group_id": str(record.get("adGroup", {}).get("id", "")),
            "event_date": segments.get("date"),
            "impressions": int(metrics.get("impressions", 0) or 0),
            "clicks": int(metrics.get("clicks", 0) or 0),
            "spend": round(micros / 1_000_000, 6),
            "conversions": float(metrics.get("conversions", 0) or 0),
            "conversion_value": float(metrics.get("conversionsValue", 0) or 0),
        }


def _integer(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None
