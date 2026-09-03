"""Transparent anomaly detection for marketing KPI time series."""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_METRICS = (
    "spend",
    "booked_revenue",
    "roas",
    "cac",
    "ctr",
    "cpc",
    "conversion_rate",
    "aov",
    "leads",
    "closed_won_conversions",
)


def detect_marketing_anomalies(
    frame: pd.DataFrame,
    *,
    entity_column: str = "normalized_channel",
    period_column: str = "reporting_month",
    metrics: tuple[str, ...] = DEFAULT_METRICS,
    rolling_window: int = 3,
    percent_threshold: float = 0.5,
    robust_z_threshold: float = 3.5,
) -> pd.DataFrame:
    """Detect deviations using prior-period change and a prior-window MAD baseline."""
    required = {entity_column, period_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    working = frame.copy()
    working[period_column] = pd.to_datetime(working[period_column], errors="coerce")
    rows: list[dict[str, object]] = []
    for entity, group in working.groupby(entity_column, dropna=False):
        group = group.sort_values(period_column)
        for metric in metrics:
            if metric not in group.columns:
                continue
            values = pd.to_numeric(group[metric], errors="coerce")
            for position in range(1, len(group)):
                current = values.iloc[position]
                prior = values.iloc[position - 1]
                if pd.isna(current):
                    continue
                history = values.iloc[max(0, position - rolling_window) : position].dropna()
                if history.empty:
                    continue
                baseline = float(history.median())
                deviation = float(current - baseline)
                pct_change = 0.0 if pd.isna(prior) or prior == 0 else float((current - prior) / abs(prior))
                mad = float(np.median(np.abs(history - baseline)))
                robust_z = 0.0 if mad == 0 else float(0.6745 * deviation / mad)
                methods = []
                if abs(pct_change) >= percent_threshold:
                    methods.append("percent_change")
                if abs(robust_z) >= robust_z_threshold:
                    methods.append("rolling_mad")
                if not methods:
                    continue
                magnitude = max(
                    abs(pct_change) / percent_threshold if percent_threshold else 0,
                    abs(robust_z) / robust_z_threshold if robust_z_threshold else 0,
                )
                severity = "high" if magnitude >= 1.6 else "medium"
                period = group.iloc[position][period_column]
                rows.append(
                    {
                        "reporting_month": period,
                        "normalized_channel": entity,
                        "entity_type": entity_column,
                        "entity_value": entity,
                        "metric_name": metric,
                        "current_value": float(current),
                        "baseline_value": baseline,
                        "prior_value": 0.0 if pd.isna(prior) else float(prior),
                        "deviation_value": deviation,
                        "pct_change": pct_change,
                        "robust_z_score": robust_z,
                        "z_score": robust_z,
                        "severity": severity,
                        "detection_method": "+".join(methods),
                        "evidence": (
                            f"{metric}={float(current):.4g}; prior={0.0 if pd.isna(prior) else float(prior):.4g}; "
                            f"rolling_median={baseline:.4g}; change={pct_change:.1%}; robust_z={robust_z:.2f}"
                        ),
                        "investigation_hint": (
                            f"Review {metric.replace('_', ' ')} against campaign mix, funnel, target, and source-quality evidence."
                        ),
                    }
                )
    columns = [
        "reporting_month",
        "normalized_channel",
        "entity_type",
        "entity_value",
        "metric_name",
        "current_value",
        "baseline_value",
        "prior_value",
        "deviation_value",
        "pct_change",
        "robust_z_score",
        "z_score",
        "severity",
        "detection_method",
        "evidence",
        "investigation_hint",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["severity", "reporting_month", "normalized_channel", "metric_name"],
        ascending=[True, False, True, True],
    ) if rows else pd.DataFrame(columns=columns)
