from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.file_io import write_frame
from ingestion.metadata import dump_json

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "google_ads": {"event_date", "campaign_id", "campaign_name", "impressions", "clicks", "spend", "conversions"},
    "facebook_ads": {"event_date", "campaign_id", "campaign_name", "reach", "clicks", "spend", "conversions"},
    "tiktok_ads": {"event_date", "campaign_id", "campaign_name", "video_views", "clicks", "spend", "conversions"},
    "website_analytics": {"event_date", "session_id", "visitor_id", "traffic_source", "device", "country"},
    "ga4_events": {"event_id", "user_pseudo_id", "session_id", "event_timestamp", "event_name", "source", "medium", "device_category", "country", "conversion_indicator", "revenue"},
    "crm_leads": {"created_at", "lead_id", "lead_source", "qualification_stage", "assigned_rep"},
    "sales_conversions": {"conversion_id", "lead_id", "conversion_date", "deal_value", "product"},
    "marketing_targets": {"target_month", "region", "channel", "target_spend", "target_revenue"},
    "campaign_mapping": {"campaign_id", "canonical_campaign_name", "canonical_channel"},
    "region_mapping": {"country", "region", "sales_territory"},
}


@dataclass(frozen=True)
class ValidationIssue:
    source_system: str
    rule_name: str
    severity: str
    failed_count: int
    sample: list[dict]


@dataclass(frozen=True)
class ValidationReport:
    source_system: str
    row_count: int
    status: str
    generated_at: str
    issues: list[ValidationIssue]

    @property
    def rejected_count(self) -> int:
        return sum(issue.failed_count for issue in self.issues if issue.severity == "error")

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["issues"] = [asdict(issue) for issue in self.issues]
        return payload


class MarketingQualityValidator:
    def validate_frame(self, source_system: str, frame: pd.DataFrame) -> tuple[ValidationReport, pd.DataFrame]:
        issues: list[ValidationIssue] = []
        rejected_masks: list[pd.Series] = []

        required = REQUIRED_COLUMNS.get(source_system, set())
        missing_columns = sorted(required - set(frame.columns))
        if missing_columns:
            issues.append(
                ValidationIssue(
                    source_system=source_system,
                    rule_name="required_columns_present",
                    severity="error",
                    failed_count=len(missing_columns),
                    sample=[{"missing_column": column} for column in missing_columns],
                )
            )

        if "event_date" in frame.columns:
            invalid = pd.to_datetime(frame["event_date"], errors="coerce").isna()
            self._append_issue(source_system, frame, issues, rejected_masks, "valid_event_date", "error", invalid)

        if "created_at" in frame.columns:
            invalid = pd.to_datetime(frame["created_at"], errors="coerce").isna()
            self._append_issue(source_system, frame, issues, rejected_masks, "valid_created_at", "error", invalid)

        if "spend" in frame.columns:
            self._append_issue(source_system, frame, issues, rejected_masks, "non_null_spend", "error", frame["spend"].isna())
            self._append_issue(source_system, frame, issues, rejected_masks, "non_negative_spend", "error", pd.to_numeric(frame["spend"], errors="coerce").fillna(0) < 0)

        if "attribution_id" in frame.columns:
            missing = frame["attribution_id"].isna() | (frame["attribution_id"].astype(str).str.strip() == "")
            self._append_issue(source_system, frame, issues, rejected_masks, "attribution_id_present", "warning", missing)

        if {"campaign_id", "event_date"}.issubset(frame.columns):
            duplicate_campaigns = frame.duplicated(subset=["campaign_id", "event_date"], keep=False)
            self._append_issue(source_system, frame, issues, rejected_masks, "duplicate_campaign_day", "warning", duplicate_campaigns)

        denominator = "impressions" if "impressions" in frame.columns else "video_views" if "video_views" in frame.columns else None
        if denominator and "clicks" in frame.columns:
            impossible = frame["clicks"].fillna(0) > frame[denominator].fillna(0)
            self._append_issue(source_system, frame, issues, rejected_masks, "clicks_not_greater_than_exposures", "error", impossible)

        if {"conversions", "clicks"}.issubset(frame.columns):
            impossible = frame["conversions"].fillna(0) > frame["clicks"].fillna(0)
            self._append_issue(source_system, frame, issues, rejected_masks, "conversions_not_greater_than_clicks", "error", impossible)

        if source_system == "sales_conversions" and "lead_id" in frame.columns:
            orphan = frame["lead_id"].isna() | frame["lead_id"].eq("UNKNOWN")
            self._append_issue(source_system, frame, issues, rejected_masks, "known_lead_id_for_conversion", "warning", orphan)

        if source_system == "website_analytics" and "device" in frame.columns:
            invalid_device = ~frame["device"].isin(["desktop", "mobile", "tablet", "unknown"])
            self._append_issue(source_system, frame, issues, rejected_masks, "known_device_mapping", "warning", invalid_device)

        if source_system == "ga4_events":
            if "event_name" in frame.columns:
                allowed = {"session_start", "page_view", "view_item", "add_to_cart", "begin_checkout", "generate_lead", "purchase"}
                invalid_event = ~frame["event_name"].isin(allowed)
                self._append_issue(source_system, frame, issues, rejected_masks, "known_ga4_event", "error", invalid_event)
            if {"event_name", "revenue"}.issubset(frame.columns):
                revenue = pd.to_numeric(frame["revenue"], errors="coerce").fillna(0)
                invalid_revenue = (frame["event_name"] != "purchase") & (revenue != 0)
                self._append_issue(source_system, frame, issues, rejected_masks, "revenue_only_on_purchase", "error", invalid_revenue)

        rejected = pd.DataFrame()
        if rejected_masks:
            combined = rejected_masks[0].copy()
            for mask in rejected_masks[1:]:
                combined = combined | mask
            rejected = frame.loc[combined].copy()

        status = "passed" if not any(issue.severity == "error" and issue.failed_count > 0 for issue in issues) else "failed"
        return (
            ValidationReport(
                source_system=source_system,
                row_count=len(frame),
                status=status,
                generated_at=datetime.now(timezone.utc).isoformat(),
                issues=issues,
            ),
            rejected,
        )

    def _append_issue(
        self,
        source_system: str,
        frame: pd.DataFrame,
        issues: list[ValidationIssue],
        rejected_masks: list[pd.Series],
        rule_name: str,
        severity: str,
        mask: pd.Series,
    ) -> None:
        failed_count = int(mask.sum())
        if failed_count == 0:
            return
        sample = frame.loc[mask].head(10).to_dict(orient="records")
        issues.append(
            ValidationIssue(
                source_system=source_system,
                rule_name=rule_name,
                severity=severity,
                failed_count=failed_count,
                sample=sample,
            )
        )
        if severity == "error":
            rejected_masks.append(mask)


def write_validation_report(report: ValidationReport, report_dir: Path, batch_id: str, source_file_stem: str) -> Path:
    path = report_dir / "validation_reports" / f"batch_id={batch_id}" / f"{source_file_stem}.json"
    dump_json(path, report.to_dict())
    return path


def write_rejected_records(rejected: pd.DataFrame, path: Path) -> Path | None:
    if rejected.empty:
        return None
    written, _ = write_frame(rejected, path, "csv")
    return written
