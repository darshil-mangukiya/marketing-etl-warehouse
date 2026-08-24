from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

try:  # Streamlit is optional for unit tests that import the loader directly.
    import streamlit as st
except Exception:  # pragma: no cover - exercised only when Streamlit is absent.
    class _StreamlitShim:
        def cache_data(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    st = _StreamlitShim()


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    label: str
    candidates: tuple[str, ...]
    required: bool = False


KNOWN_DATA_DIRS = (
    PROJECT_ROOT / "data" / "exports",
    PROJECT_ROOT / "reports" / "generated" / "excel_ready",
    PROJECT_ROOT / "reports" / "generated",
    PROJECT_ROOT / "release" / "site" / "data",
    PROJECT_ROOT / "monitoring" / "generated",
    PROJECT_ROOT / "governance" / "generated",
)

DATASET_SPECS: dict[str, DatasetSpec] = {
    "executive_scorecard": DatasetSpec(
        "executive_scorecard",
        "Executive scorecard",
        ("demo_mart_executive_scorecard.csv",),
    ),
    "channel_performance": DatasetSpec(
        "channel_performance",
        "Channel performance mart",
        ("demo_mart_channel_performance.csv", "channel_variance_analysis.csv"),
        required=True,
    ),
    "campaign_performance": DatasetSpec(
        "campaign_performance",
        "Campaign performance mart",
        ("demo_mart_campaign_performance.csv", "campaign_roi_analysis.csv"),
        required=True,
    ),
    "campaign_optimization": DatasetSpec(
        "campaign_optimization",
        "Campaign optimization mart",
        ("demo_mart_campaign_optimization.csv",),
    ),
    "funnel_performance": DatasetSpec(
        "funnel_performance",
        "Funnel performance mart",
        ("demo_mart_funnel_performance.csv", "funnel_conversion_analysis.csv"),
        required=True,
    ),
    "journey_quality": DatasetSpec(
        "journey_quality",
        "Journey quality mart",
        ("demo_mart_journey_quality.csv",),
    ),
    "attribution_summary": DatasetSpec(
        "attribution_summary",
        "Attribution summary mart",
        ("demo_mart_attribution_summary.csv",),
        required=True,
    ),
    "attribution_model_comparison": DatasetSpec(
        "attribution_model_comparison",
        "Attribution model comparison mart",
        ("demo_mart_attribution_model_comparison.csv",),
    ),
    "attribution_reconciliation": DatasetSpec(
        "attribution_reconciliation",
        "Attribution reconciliation mart",
        ("demo_mart_attribution_reconciliation.csv",),
    ),
    "conversion_lag": DatasetSpec(
        "conversion_lag",
        "Conversion lag mart",
        ("demo_mart_conversion_lag.csv",),
    ),
    "target_vs_actual": DatasetSpec(
        "target_vs_actual",
        "Target vs actual mart",
        ("demo_mart_target_vs_actual.csv", "target_vs_actual_analysis.csv"),
        required=True,
    ),
    "budget_pacing": DatasetSpec(
        "budget_pacing",
        "Budget pacing mart",
        ("demo_mart_budget_pacing.csv",),
    ),
    "budget_efficiency": DatasetSpec(
        "budget_efficiency",
        "Budget efficiency mart",
        ("demo_mart_budget_efficiency.csv",),
    ),
    "customer_value": DatasetSpec(
        "customer_value",
        "Customer value mart",
        ("demo_mart_customer_value.csv",),
    ),
    "customer_segment_mix": DatasetSpec(
        "customer_segment_mix",
        "Customer segment mix mart",
        ("demo_mart_customer_segment_mix.csv",),
    ),
    "data_quality_monitoring": DatasetSpec(
        "data_quality_monitoring",
        "Data quality monitoring mart",
        ("demo_mart_data_quality_monitoring.csv", "data_quality_summary.csv"),
        required=True,
    ),
    "source_health": DatasetSpec(
        "source_health",
        "Source health mart",
        ("demo_mart_source_health.csv",),
        required=True,
    ),
    "device_performance": DatasetSpec(
        "device_performance",
        "Device performance mart",
        ("demo_mart_device_performance.csv",),
    ),
}

DATE_COLUMN_NAMES = {
    "reporting_month",
    "target_month",
    "snapshot_month",
    "forecast_month",
    "cohort_month",
    "activity_month",
    "load_date",
    "ingestion_time",
    "watermark_captured_at",
}


def normalize_column_name(column: str) -> str:
    value = str(column).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output.columns = [normalize_column_name(column) for column in output.columns]
    return output


def parse_dates(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in output.columns:
        if (
            column in DATE_COLUMN_NAMES
            or column.endswith("_date")
            or column.endswith("_month")
            or column.endswith("_at")
            or column.endswith("_watermark")
        ):
            output[column] = pd.to_datetime(output[column], errors="coerce")
    return output


def _read_data_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".json", ".jsonl"}:
        try:
            return pd.read_json(path, lines=suffix == ".jsonl")
        except ValueError:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return pd.json_normalize(payload)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.DataFrame()


def find_data_file(candidates: Iterable[str], search_dirs: Iterable[Path | str] | None = None) -> Path | None:
    directories = tuple(Path(directory) for directory in (search_dirs or KNOWN_DATA_DIRS))
    for directory in directories:
        for candidate in candidates:
            path = directory / candidate
            if path.exists():
                return path
    return None


def load_optional_dataset(
    dataset_key: str,
    search_dirs: Iterable[Path | str] | None = None,
) -> pd.DataFrame:
    spec = DATASET_SPECS.get(
        dataset_key,
        DatasetSpec(dataset_key, dataset_key.replace("_", " ").title(), (f"{dataset_key}.csv",)),
    )
    path = find_data_file(spec.candidates, search_dirs)
    if path is None:
        frame = pd.DataFrame()
        frame.attrs["missing"] = True
        frame.attrs["dataset_label"] = spec.label
        return frame

    try:
        frame = parse_dates(normalize_columns(_read_data_file(path)))
    except Exception as exc:  # Defensive: one bad optional file should not break the app.
        frame = pd.DataFrame()
        frame.attrs["load_error"] = str(exc)

    frame.attrs["source_path"] = str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path)
    frame.attrs["dataset_label"] = spec.label
    return frame


def ensure_demo_marts() -> None:
    required_missing = [
        spec
        for spec in DATASET_SPECS.values()
        if spec.required and find_data_file(spec.candidates, (PROJECT_ROOT / "data" / "exports",)) is None
    ]
    if not required_missing:
        return

    try:
        from scripts.build_demo_marts import build_demo_marts

        build_demo_marts()
    except Exception:
        return


@st.cache_data(show_spinner=False)
def load_dashboard_datasets() -> dict[str, pd.DataFrame]:
    ensure_demo_marts()
    return {key: load_optional_dataset(key) for key in DATASET_SPECS}


def source_note(frame: pd.DataFrame) -> str:
    label = frame.attrs.get("dataset_label", "Dataset")
    path = frame.attrs.get("source_path")
    if path:
        return f"{label}: `{path}`"
    if frame.attrs.get("missing"):
        return f"{label}: missing optional input"
    if frame.attrs.get("load_error"):
        return f"{label}: could not load input"
    return label


def available_values(frames: Iterable[pd.DataFrame], columns: Iterable[str]) -> list[str]:
    values: set[str] = set()
    for frame in frames:
        if frame.empty:
            continue
        for column in columns:
            if column in frame.columns:
                values.update(str(value) for value in frame[column].dropna().unique().tolist() if str(value).strip())
    return sorted(values)


def apply_date_filter(
    frame: pd.DataFrame,
    date_range: tuple[pd.Timestamp, pd.Timestamp] | None,
    columns: Iterable[str] = ("reporting_month", "target_month", "snapshot_month"),
) -> pd.DataFrame:
    if frame.empty or date_range is None:
        return frame
    start, end = date_range
    output = frame
    masks = []
    for column in columns:
        if column in output.columns:
            masks.append(output[column].between(start, end, inclusive="both"))
    if not masks:
        return output
    mask = masks[0]
    for extra_mask in masks[1:]:
        mask = mask | extra_mask
    return output[mask]


def apply_value_filter(frame: pd.DataFrame, values: list[str], columns: Iterable[str]) -> pd.DataFrame:
    if frame.empty or not values:
        return frame
    output = frame
    masks = []
    for column in columns:
        if column in output.columns:
            masks.append(output[column].astype(str).isin(values))
    if not masks:
        return output
    mask = masks[0]
    for extra_mask in masks[1:]:
        mask = mask | extra_mask
    return output[mask]


def apply_text_search(frame: pd.DataFrame, search_text: str, columns: Iterable[str]) -> pd.DataFrame:
    if frame.empty or not search_text.strip():
        return frame
    mask = pd.Series(False, index=frame.index)
    for column in columns:
        if column in frame.columns:
            mask = mask | frame[column].astype(str).str.contains(search_text, case=False, na=False)
    return frame[mask]
