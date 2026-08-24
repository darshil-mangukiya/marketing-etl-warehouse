import pandas as pd

from ingestion.validators import MarketingQualityValidator


def test_validator_flags_impossible_paid_media_kpis() -> None:
    frame = pd.DataFrame(
        [
            {
                "event_date": "2025-01-01",
                "campaign_id": "CMP-000001",
                "campaign_name": "Brand Search",
                "impressions": 100,
                "clicks": 150,
                "spend": None,
                "conversions": 10,
            }
        ]
    )
    report, rejected = MarketingQualityValidator().validate_frame("google_ads", frame)

    assert report.status == "failed"
    assert {"non_null_spend", "clicks_not_greater_than_exposures"}.issubset(
        {issue.rule_name for issue in report.issues}
    )
    assert len(rejected) == 1


def test_validator_allows_clean_target_rows() -> None:
    frame = pd.DataFrame(
        [
            {
                "target_month": "2025-01",
                "region": "NA",
                "channel": "paid_search",
                "target_spend": 1000,
                "target_revenue": 5000,
            }
        ]
    )
    report, rejected = MarketingQualityValidator().validate_frame("marketing_targets", frame)

    assert report.status == "passed"
    assert rejected.empty
