from __future__ import annotations

from connectors.base import BaseMarketingConnector
from connectors.models import ExtractionWindow, PageResult


class MetaAdsConnector(BaseMarketingConnector):
    source_system = "meta_ads"
    endpoint = "insights"

    def __init__(self, base_url: str, access_token: str, account_id: str, **kwargs: object) -> None:
        super().__init__(base_url, access_token, **kwargs)
        self.account_id = account_id

    def request_params(self, window: ExtractionWindow, page_token: str | None, page_size: int) -> dict:
        return {"account_id": self.account_id, "since": window.start_date.isoformat(), "until": window.end_date.isoformat(), "after": page_token, "limit": page_size}

    def parse_page(self, payload: dict, headers: dict[str, str]) -> PageResult:
        records = payload.get("data", [])
        if not isinstance(records, list):
            raise ValueError("Malformed Meta response: data must be a list.")
        return PageResult(records, payload.get("paging", {}).get("cursors", {}).get("after"), headers.get("x-fb-trace-id"))

    def normalize(self, record: dict) -> dict:
        actions = {item.get("action_type"): float(item.get("value", 0)) for item in record.get("actions", [])}
        return {
            **self.metadata(self.source_system),
            "account_id": self.account_id,
            "campaign_id": str(record.get("campaign_id", "")),
            "campaign_name": record.get("campaign_name"),
            "ad_group_id": str(record.get("adset_id", "")),
            "event_date": record.get("date_start"),
            "impressions": int(record.get("impressions", 0) or 0),
            "clicks": int(record.get("clicks", 0) or 0),
            "spend": float(record.get("spend", 0) or 0),
            "conversions": actions.get("purchase", actions.get("lead", 0.0)),
            "conversion_value": actions.get("purchase_roas", 0.0),
        }
