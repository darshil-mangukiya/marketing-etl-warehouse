from __future__ import annotations

import pandas as pd

from bi_app.data_loader import load_optional_dataset, normalize_columns
from bi_app.metrics import campaign_recommendation, executive_kpis


def test_data_loader_handles_missing_files(tmp_path) -> None:
    frame = load_optional_dataset("missing_dataset", search_dirs=[tmp_path])

    assert frame.empty
    assert frame.attrs["missing"] is True


def test_loader_normalizes_columns_from_csv(tmp_path) -> None:
    path = tmp_path / "custom_dataset.csv"
    path.write_text("Campaign Name,Booked Revenue,Reporting Month\nSearch Brand,1200,2025-01-01\n")

    frame = load_optional_dataset("custom_dataset", search_dirs=[tmp_path])

    assert list(frame.columns) == ["campaign_name", "booked_revenue", "reporting_month"]
    assert pd.api.types.is_datetime64_any_dtype(frame["reporting_month"])
    assert frame.iloc[0]["booked_revenue"] == 1200


def test_normalize_columns_handles_spaces_and_punctuation() -> None:
    frame = pd.DataFrame({" Spend ($) ": [10], "ROAS%": [2.5]})

    normalized = normalize_columns(frame)

    assert list(normalized.columns) == ["spend", "roas"]


def test_metrics_handle_empty_dataframes() -> None:
    kpis = executive_kpis(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    assert kpis["total_spend"] == 0
    assert kpis["roas"] == 0
    assert kpis["data_quality_status"] == "Unknown"


def test_campaign_recommendation_labels_are_threshold_based() -> None:
    assert campaign_recommendation({"spend": 1000, "conversions": 20, "attributed_roas": 3.0}) == "Scale"
    assert campaign_recommendation({"spend": 5000, "conversions": 3, "attributed_roas": 0.5}, median_spend=1000) == "Pause Candidate"
    assert campaign_recommendation({"spend": 1000, "conversions": 5, "attributed_revenue": 0}) == "Optimize"
    assert campaign_recommendation({"spend": 1000, "conversions": 5, "attributed_roas": 1.5}) == "Monitor"
