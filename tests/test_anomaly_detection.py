import pandas as pd

from analytics.anomaly_detection import detect_marketing_anomalies


def test_anomaly_detector_returns_method_baseline_and_evidence() -> None:
    frame = pd.DataFrame(
        {
            "reporting_month": pd.date_range("2026-01-01", periods=4, freq="MS"),
            "normalized_channel": ["paid_search"] * 4,
            "spend": [100, 102, 101, 250],
            "roas": [3.0, 3.1, 3.0, 1.0],
        }
    )

    result = detect_marketing_anomalies(frame, metrics=("spend", "roas"))

    assert {"spend", "roas"}.issubset(set(result["metric_name"]))
    assert result["detection_method"].str.len().gt(0).all()
    assert result["evidence"].str.contains("rolling_median").all()
    assert result["baseline_value"].notna().all()


def test_anomaly_detector_returns_empty_contract_for_stable_series() -> None:
    frame = pd.DataFrame(
        {
            "reporting_month": pd.date_range("2026-01-01", periods=4, freq="MS"),
            "normalized_channel": ["paid_social"] * 4,
            "spend": [100, 101, 99, 100],
        }
    )

    result = detect_marketing_anomalies(frame, metrics=("spend",))

    assert result.empty
    assert "detection_method" in result.columns
