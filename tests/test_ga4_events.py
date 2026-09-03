from __future__ import annotations

import pandas as pd
import pytest

from data_sources.generators import SyntheticMarketingGenerator
from ingestion.validators import MarketingQualityValidator

REQUIRED_EVENTS = {"session_start", "page_view", "view_item", "add_to_cart", "begin_checkout", "generate_lead", "purchase"}


def test_ga4_generator_emits_realistic_event_schema(tmp_path) -> None:
    frame = SyntheticMarketingGenerator("2025-01-01", "2025-01-31", tmp_path, seed=11).ga4_events(2000)
    required = {
        "event_id", "user_pseudo_id", "session_id", "event_timestamp", "event_name", "source", "medium", "campaign", "landing_page", "device_category", "region", "country", "product", "engagement_indicator", "conversion_indicator", "revenue"
    }
    assert required.issubset(frame.columns)
    assert REQUIRED_EVENTS.issubset(set(frame["event_name"]))
    assert frame["event_id"].notna().all()


def test_ga4_revenue_and_conversion_semantics(tmp_path) -> None:
    frame = SyntheticMarketingGenerator("2025-01-01", "2025-01-31", tmp_path, seed=12).ga4_events(1000)
    assert (frame.loc[frame["event_name"] != "purchase", "revenue"] == 0).all()
    assert (frame.loc[frame["event_name"].isin(["generate_lead", "purchase"]), "conversion_indicator"] == 1).all()


def test_ga4_validator_rejects_unknown_events_and_non_purchase_revenue() -> None:
    frame = pd.DataFrame(
        [{
            "event_id": "e1", "user_pseudo_id": "u1", "session_id": "s1", "event_timestamp": "2025-01-01T00:00:00Z", "event_date": "2025-01-01", "event_name": "unexpected", "source": "direct", "medium": "none", "device_category": "mobile", "country": "US", "conversion_indicator": 0, "revenue": 9.0,
        }]
    )
    report, rejected = MarketingQualityValidator().validate_frame("ga4_events", frame)
    assert report.status == "failed"
    assert len(rejected) == 1


def test_ga4_session_rollup_logic_is_reconcilable(tmp_path) -> None:
    frame = SyntheticMarketingGenerator("2025-01-01", "2025-01-02", tmp_path, seed=13).ga4_events(500)
    sessions = frame.groupby("session_id", as_index=False).agg(event_count=("event_id", "count"), revenue=("revenue", "sum"))
    assert sessions["event_count"].sum() == len(frame)
    assert sessions["revenue"].sum() == pytest.approx(frame["revenue"].sum())
