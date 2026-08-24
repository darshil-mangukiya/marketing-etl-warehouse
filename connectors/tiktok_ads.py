from __future__ import annotations

from connectors.base import BaseMarketingConnector
from connectors.models import ExtractionWindow, PageResult


class TikTokAdsConnector(BaseMarketingConnector):
    source_system = "tiktok_ads"
    endpoint = "report/integrated/get"

    def __init__(self, base_url: str, access_token: str, advertiser_id: str, **kwargs: object) -> None:
        super().__init__(base_url, access_token, **kwargs)
        self.advertiser_id = advertiser_id

    def request_params(self, window: ExtractionWindow, page_token: str | None, page_size: int) -> dict:
        return {"advertiser_id": self.advertiser_id, "start_date": window.start_date.isoformat(), "end_date": window.end_date.isoformat(), "page": int(page_token or 1), "page_size": page_size}

    def parse_page(self, payload: dict, headers: dict[str, str]) -> PageResult:
        if int(payload.get("code", 0)) != 0:
            raise ValueError("TikTok API returned a non-success code; message was redacted.")
        data = payload.get("data", {})
        records = data.get("list", [])
        if not isinstance(records, list):
            raise ValueError("Malformed TikTok response: data.list must be a list.")
        page_info = data.get("page_info", {})
        page = int(page_info.get("page", 1))
        total_pages = int(page_info.get("total_page", page))
        return PageResult(records, str(page + 1) if page < total_pages else None, headers.get("log-id"))

    def normalize(self, record: dict) -> dict:
        dimensions = record.get("dimensions", {})
        metrics = record.get("metrics", {})
        return {
            **self.metadata(self.source_system),
            "account_id": self.advertiser_id,
            "campaign_id": str(dimensions.get("campaign_id", "")),
            "campaign_name": dimensions.get("campaign_name"),
            "ad_group_id": str(dimensions.get("adgroup_id", "")),
            "event_date": dimensions.get("stat_time_day"),
            "impressions": int(metrics.get("impressions", 0) or 0),
            "clicks": int(metrics.get("clicks", 0) or 0),
            "spend": float(metrics.get("spend", 0) or 0),
            "conversions": float(metrics.get("conversion", 0) or 0),
            "conversion_value": float(metrics.get("total_purchase_value", 0) or 0),
        }
