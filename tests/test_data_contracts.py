import pandas as pd

from ingestion.data_contracts import validate_frame_against_contract


def test_contract_validator_flags_missing_columns() -> None:
    issues = validate_frame_against_contract(
        "google_ads",
        pd.DataFrame([{"event_date": "2025-01-01"}]),
        {
            "required_columns": {
                "event_date": "date",
                "campaign_id": "string",
            },
            "primary_key": ["event_date", "campaign_id"],
        },
    )

    assert any(issue.rule_name == "required_columns" for issue in issues)


def test_contract_validator_flags_business_rule_failure() -> None:
    issues = validate_frame_against_contract(
        "google_ads",
        pd.DataFrame([{"clicks": 20, "impressions": 10}]),
        {
            "required_columns": {"clicks": "integer", "impressions": "integer"},
            "rules": [{"name": "clicks_lte_impressions", "expression": "clicks <= impressions"}],
        },
    )

    assert any(issue.rule_name == "clicks_lte_impressions" and issue.failed_count == 1 for issue in issues)
