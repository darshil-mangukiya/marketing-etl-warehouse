from __future__ import annotations

import argparse
import json
import math
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "source_volume.yml"


@dataclass(frozen=True)
class GeneratedPart:
    source_system: str
    path: str
    row_count: int
    file_format: str
    chunk_number: int


@dataclass(frozen=True)
class GenerationManifest:
    batch_id: str
    profile: str
    generated_at: str
    parts: list[GeneratedPart]

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "profile": self.profile,
            "generated_at": self.generated_at,
            "parts": [part.__dict__ for part in self.parts],
        }


class SyntheticMarketingGenerator:
    """Chunked synthetic data generator for marketing, funnel, and revenue systems."""

    def __init__(
        self,
        start_date: str,
        end_date: str,
        output_root: str | Path,
        seed: int = 42,
    ) -> None:
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.output_root = Path(output_root)
        if not self.output_root.is_absolute():
            self.output_root = PROJECT_ROOT / self.output_root
        self.rng = np.random.default_rng(seed)
        self.date_range = pd.date_range(self.start_date, self.end_date, freq="D")

        self.regions = np.array(["NA", "LATAM", "EMEA", "APAC"])
        self.countries = np.array(["US", "CA", "MX", "BR", "GB", "DE", "FR", "IN", "JP", "AU"])
        self.devices = np.array(["desktop", "mobile", "tablet", "unknown"])
        self.products = np.array(["Starter", "Growth", "Enterprise", "Commerce Pro", "Marketing Suite"])
        self.reps = np.array([f"rep_{i:03d}" for i in range(1, 81)])
        self.attribution_pool_size = 50000
        self.campaign_templates = np.array(
            [
                "Brand Search",
                "Competitor Search",
                "Retargeting",
                "Lifecycle Winback",
                "Holiday Promo",
                "Creator Spark",
                "Product Launch",
                "Enterprise ABM",
                "Cart Recovery",
                "Regional Expansion",
            ]
        )
        self.channel_weights = np.array([0.28, 0.22, 0.14, 0.12, 0.11, 0.08, 0.05])

    def generate_all(
        self,
        profile: str,
        row_counts: dict[str, int],
        formats: dict[str, str],
        chunk_size: int,
        clean: bool = True,
    ) -> GenerationManifest:
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        if clean and self.output_root.exists():
            shutil.rmtree(self.output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

        generators: dict[str, Callable[[int], pd.DataFrame]] = {
            "google_ads": self.google_ads,
            "facebook_ads": self.facebook_ads,
            "tiktok_ads": self.tiktok_ads,
            "website_analytics": self.website_analytics,
            "ga4_events": self.ga4_events,
            "crm_leads": self.crm_leads,
            "sales_conversions": self.sales_conversions,
            "marketing_targets": self.marketing_targets,
        }

        parts: list[GeneratedPart] = []
        for source_system, rows in row_counts.items():
            source_format = formats.get(source_system, "csv")
            if source_system not in generators:
                raise ValueError(f"No generator registered for source {source_system}")
            parts.extend(
                self._write_source(
                    source_system=source_system,
                    batch_id=batch_id,
                    rows=rows,
                    chunk_size=chunk_size,
                    preferred_format=source_format,
                    factory=generators[source_system],
                )
            )

        parts.extend(self._write_reference_sources(batch_id=batch_id))

        manifest = GenerationManifest(
            batch_id=batch_id,
            profile=profile,
            generated_at=datetime.now(timezone.utc).isoformat(),
            parts=parts,
        )
        manifest_path = self.output_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
        return manifest

    def _write_source(
        self,
        source_system: str,
        batch_id: str,
        rows: int,
        chunk_size: int,
        preferred_format: str,
        factory: Callable[[int], pd.DataFrame],
    ) -> list[GeneratedPart]:
        source_dir = self.output_root / f"source_system={source_system}" / f"batch_id={batch_id}"
        source_dir.mkdir(parents=True, exist_ok=True)
        chunks = max(1, math.ceil(rows / chunk_size))
        parts: list[GeneratedPart] = []
        for chunk_number in range(chunks):
            current_rows = min(chunk_size, rows - chunk_number * chunk_size)
            if current_rows <= 0:
                break
            frame = factory(current_rows)
            frame.insert(0, "source_system", source_system)
            frame.insert(1, "batch_id", batch_id)
            frame["ingestion_available_at"] = datetime.now(timezone.utc).isoformat()
            path, actual_format = write_partition(
                frame=frame,
                output_dir=source_dir,
                source_system=source_system,
                chunk_number=chunk_number,
                preferred_format=preferred_format,
            )
            parts.append(
                GeneratedPart(
                    source_system=source_system,
                    path=manifest_path(path),
                    row_count=len(frame),
                    file_format=actual_format,
                    chunk_number=chunk_number,
                )
            )
        return parts

    def _write_reference_sources(self, batch_id: str) -> list[GeneratedPart]:
        campaign_ids = [f"CMP-{i:06d}" for i in range(1, 501)]
        mapping = pd.DataFrame(
            {
                "source_system": "reference",
                "batch_id": batch_id,
                "campaign_id": campaign_ids,
                "canonical_campaign_name": [
                    f"{self.campaign_templates[i % len(self.campaign_templates)]} {2024 + (i % 2)}"
                    for i in range(len(campaign_ids))
                ],
                "canonical_channel": self.rng.choice(
                    ["paid_search", "paid_social", "email", "organic", "direct"],
                    size=len(campaign_ids),
                    p=[0.33, 0.31, 0.14, 0.13, 0.09],
                ),
                "owner_team": self.rng.choice(
                    ["growth", "performance_marketing", "lifecycle", "brand"],
                    size=len(campaign_ids),
                ),
                "valid_from": "2024-01-01",
                "valid_to": None,
            }
        )
        regions = pd.DataFrame(
            {
                "source_system": "reference",
                "batch_id": batch_id,
                "country": self.countries,
                "region": ["NA", "NA", "LATAM", "LATAM", "EMEA", "EMEA", "EMEA", "APAC", "APAC", "APAC"],
                "sales_territory": [
                    "North America",
                    "North America",
                    "Latin America",
                    "Latin America",
                    "Europe",
                    "Europe",
                    "Europe",
                    "Asia Pacific",
                    "Asia Pacific",
                    "Asia Pacific",
                ],
            }
        )
        parts: list[GeneratedPart] = []
        for name, frame in {"campaign_mapping": mapping, "region_mapping": regions}.items():
            ref_dir = self.output_root / f"source_system={name}" / f"batch_id={batch_id}"
            path, actual_format = write_partition(frame, ref_dir, name, 0, "csv")
            parts.append(
                GeneratedPart(
                    source_system=name,
                    path=manifest_path(path),
                    row_count=len(frame),
                    file_format=actual_format,
                    chunk_number=0,
                )
            )
        return parts

    def google_ads(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        impressions = self.rng.integers(40, 18000, rows)
        ctr = self.rng.beta(2.2, 45, rows) + self._seasonality(dates) / 120
        clicks = np.maximum(0, (impressions * ctr).astype(int))
        cpc = self.rng.lognormal(mean=0.92, sigma=0.45, size=rows)
        spend = clicks * cpc
        conversions = self.rng.binomial(np.maximum(clicks, 1), np.clip(self.rng.beta(1.7, 38, rows), 0, 0.35))
        frame = pd.DataFrame(
            {
                "event_date": dates.strftime("%Y-%m-%d"),
                "campaign_id": self._campaign_ids(rows),
                "campaign_name": self._campaign_names(rows),
                "ad_group_id": [f"GAG-{value:08d}" for value in self.rng.integers(1, 250000, rows)],
                "network_type": self.rng.choice(["search", "display", "youtube", "partner"], rows),
                "region": self.rng.choice(self.regions, rows, p=[0.48, 0.13, 0.25, 0.14]),
                "currency": self.rng.choice(["USD", "USD", "USD", "EUR", "GBP"], rows),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": safe_divide(clicks, impressions),
                "avg_cpc": cpc.round(4),
                "spend": spend.round(2),
                "conversions": conversions,
                "attribution_id": self._attribution_ids(rows, missing_rate=0.04),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )
        return self._inject_paid_media_defects(frame, spend_column="spend")

    def facebook_ads(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        reach = self.rng.integers(80, 45000, rows)
        frequency = self.rng.uniform(1.0, 4.8, rows)
        impressions = (reach * frequency).astype(int)
        clicks = self.rng.binomial(impressions, np.clip(self.rng.beta(1.8, 58, rows), 0, 0.28))
        spend = clicks * self.rng.lognormal(mean=0.55, sigma=0.5, size=rows)
        frame = pd.DataFrame(
            {
                "event_date": dates.strftime("%Y-%m-%d"),
                "campaign_id": self._campaign_ids(rows),
                "campaign_name": self._campaign_names(rows, social=True),
                "ad_set_id": [f"FAS-{value:08d}" for value in self.rng.integers(1, 200000, rows)],
                "placement": self.rng.choice(["feed", "stories", "reels", "audience_network"], rows),
                "country": self.rng.choice(self.countries, rows),
                "reach": reach,
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend.round(2),
                "conversions": self.rng.binomial(np.maximum(clicks, 1), np.clip(self.rng.beta(1.3, 46, rows), 0, 0.25)),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.06),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )
        drift_mask = self.rng.random(rows) < 0.08
        frame.loc[drift_mask, "campaign_objective"] = self.rng.choice(
            ["traffic", "conversions", "lead_generation"], drift_mask.sum()
        )
        return self._inject_paid_media_defects(frame, spend_column="spend")

    def tiktok_ads(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        video_views = self.rng.integers(200, 85000, rows)
        clicks = self.rng.binomial(video_views, np.clip(self.rng.beta(1.1, 85, rows), 0, 0.18))
        spend = clicks * self.rng.lognormal(mean=0.35, sigma=0.55, size=rows)
        frame = pd.DataFrame(
            {
                "event_date": dates.strftime("%Y-%m-%d"),
                "campaign_id": self._campaign_ids(rows),
                "campaign_name": self._campaign_names(rows, social=True),
                "creative_id": [f"TTK-{value:08d}" for value in self.rng.integers(1, 500000, rows)],
                "country": self.rng.choice(self.countries, rows),
                "video_views": video_views,
                "clicks": clicks,
                "spend": spend.round(2),
                "conversions": self.rng.binomial(np.maximum(clicks, 1), np.clip(self.rng.beta(1.0, 52, rows), 0, 0.22)),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.08),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )
        return self._inject_paid_media_defects(frame, spend_column="spend")

    def website_analytics(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        channels = np.array(["google_ads", "facebook_ads", "tiktok_ads", "email", "organic_search", "direct", "referral"])
        sessions = pd.DataFrame(
            {
                "event_date": dates.strftime("%Y-%m-%d"),
                "session_id": [f"SES-{value:012d}" for value in self.rng.integers(1, 999999999999, rows)],
                "visitor_id": [f"VIS-{value:010d}" for value in self.rng.integers(1, 25000000, rows)],
                "utm_campaign_id": self._campaign_ids(rows, missing_rate=0.11),
                "utm_campaign": self._campaign_names(rows),
                "traffic_source": self.rng.choice(channels, rows, p=self.channel_weights),
                "device": self.rng.choice(self.devices, rows, p=[0.42, 0.48, 0.08, 0.02]),
                "country": self.rng.choice(self.countries, rows),
                "page_views": self.rng.poisson(3.2, rows) + 1,
                "session_duration_seconds": self.rng.gamma(shape=2.4, scale=58, size=rows).round(0).astype(int),
                "bounce_flag": self.rng.binomial(1, 0.34, rows),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.09),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )
        sessions.loc[self.rng.random(rows) < 0.01, "device"] = "other"
        return sessions

    def ga4_events(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        event_names = np.array(
            ["session_start", "page_view", "view_item", "add_to_cart", "begin_checkout", "generate_lead", "purchase"]
        )
        event_probabilities = [0.18, 0.39, 0.16, 0.08, 0.06, 0.07, 0.06]
        events = self.rng.choice(event_names, rows, p=event_probabilities)
        sources = np.array(["google", "facebook", "tiktok", "newsletter", "google", "(direct)", "partner"])
        source = self.rng.choice(sources, rows, p=self.channel_weights)
        medium_lookup = {
            "google": "cpc",
            "facebook": "paid_social",
            "tiktok": "paid_social",
            "newsletter": "email",
            "(direct)": "(none)",
            "partner": "referral",
        }
        event_seconds = self.rng.integers(0, 86400, rows)
        event_timestamps = pd.to_datetime(dates) + pd.to_timedelta(event_seconds, unit="s")
        purchase_mask = events == "purchase"
        conversion_mask = np.isin(events, ["generate_lead", "purchase"])
        revenue = np.zeros(rows)
        revenue[purchase_mask] = self.rng.lognormal(mean=6.7, sigma=0.55, size=int(purchase_mask.sum()))
        return pd.DataFrame(
            {
                "event_id": [f"EVT-{value:014d}" for value in self.rng.integers(1, 99999999999999, rows)],
                "user_pseudo_id": [f"UPI-{value:011d}" for value in self.rng.integers(1, 40000000000, rows)],
                "session_id": [f"GA4-{value:012d}" for value in self.rng.integers(1, 999999999999, rows)],
                "event_timestamp": event_timestamps.astype(str),
                "event_date": event_timestamps.strftime("%Y-%m-%d"),
                "event_name": events,
                "source": source,
                "medium": [medium_lookup[value] for value in source],
                "campaign": self._campaign_names(rows),
                "campaign_id": self._campaign_ids(rows, missing_rate=0.12),
                "landing_page": self.rng.choice(["/", "/pricing", "/demo", "/products/growth", "/resources"], rows),
                "device_category": self.rng.choice(self.devices[:3], rows, p=[0.42, 0.50, 0.08]),
                "region": self.rng.choice(self.regions, rows),
                "country": self.rng.choice(self.countries, rows),
                "product": self.rng.choice(self.products, rows),
                "engagement_indicator": np.isin(events, ["view_item", "add_to_cart", "begin_checkout", "generate_lead", "purchase"]).astype(int),
                "conversion_indicator": conversion_mask.astype(int),
                "revenue": revenue.round(2),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.08),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )

    def crm_leads(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        stages = np.array(["new", "marketing_qualified", "sales_accepted", "sales_qualified", "disqualified"])
        lead_scores = np.clip(self.rng.normal(62, 21, rows), 0, 100).round(1)
        frame = pd.DataFrame(
            {
                "created_at": dates.astype(str),
                "lead_id": [f"LEAD-{value:010d}" for value in self.rng.integers(1, 20000000, rows)],
                "customer_id": [f"CUST-{value:010d}" for value in self.rng.integers(1, 12000000, rows)],
                "lead_source": self.rng.choice(
                    ["Google Ads", "facebook", "Tik Tok", "Email", "Organic", "Direct", "Referral", None],
                    rows,
                    p=[0.25, 0.2, 0.12, 0.13, 0.12, 0.08, 0.07, 0.03],
                ),
                "campaign_id": self._campaign_ids(rows, missing_rate=0.07),
                "qualification_stage": self.rng.choice(stages, rows, p=[0.39, 0.24, 0.13, 0.11, 0.13]),
                "lead_score": lead_scores,
                "assigned_rep": self.rng.choice(self.reps, rows),
                "region": self.rng.choice(self.regions, rows),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.12),
                "cdc_operation": self.rng.choice(["I", "U", "D"], rows, p=[0.88, 0.105, 0.015]),
                "updated_at": self._updated_at(dates).astype(str),
            }
        )
        duplicate_mask = self.rng.random(rows) < 0.015
        frame.loc[duplicate_mask, "lead_id"] = frame.loc[duplicate_mask, "lead_id"].shift(1).fillna(frame["lead_id"])
        return frame

    def sales_conversions(self, rows: int) -> pd.DataFrame:
        dates = self._event_dates(rows)
        lag = self.rng.integers(0, 91, rows)
        conversion_dates = pd.to_datetime(dates) + pd.to_timedelta(lag, unit="D")
        deal_value = self.rng.lognormal(mean=7.9, sigma=0.65, size=rows).round(2)
        frame = pd.DataFrame(
            {
                "conversion_id": [f"CNV-{value:011d}" for value in self.rng.integers(1, 90000000000, rows)],
                "lead_id": [f"LEAD-{value:010d}" for value in self.rng.integers(1, 20000000, rows)],
                "customer_id": [f"CUST-{value:010d}" for value in self.rng.integers(1, 12000000, rows)],
                "created_at": dates.astype(str),
                "conversion_date": conversion_dates.strftime("%Y-%m-%d"),
                "product": self.rng.choice(self.products, rows, p=[0.28, 0.31, 0.16, 0.13, 0.12]),
                "deal_value": deal_value,
                "gross_margin": (deal_value * self.rng.uniform(0.48, 0.86, rows)).round(2),
                "currency": self.rng.choice(["USD", "USD", "USD", "EUR", "GBP"], rows),
                "attribution_id": self._attribution_ids(rows, missing_rate=0.1),
                "campaign_id": self._campaign_ids(rows, missing_rate=0.09),
                "cdc_operation": self.rng.choice(["I", "U", "D"], rows, p=[0.9, 0.085, 0.015]),
                "updated_at": self._updated_at(conversion_dates).astype(str),
            }
        )
        frame.loc[self.rng.random(rows) < 0.025, "lead_id"] = "UNKNOWN"
        return frame

    def marketing_targets(self, rows: int) -> pd.DataFrame:
        months = pd.period_range(self.start_date, self.end_date, freq="M").astype(str)
        channels = np.array(["paid_search", "paid_social", "email", "organic", "direct"])
        records = []
        while len(records) < rows:
            for month in months:
                for region in self.regions:
                    for channel in channels:
                        records.append(
                            {
                                "target_month": month,
                                "region": region,
                                "channel": channel,
                                "target_spend": round(float(self.rng.uniform(18000, 420000)), 2),
                                "target_revenue": round(float(self.rng.uniform(75000, 1200000)), 2),
                                "target_leads": int(self.rng.integers(250, 15000)),
                                "target_conversions": int(self.rng.integers(25, 2500)),
                                "budget_owner": self.rng.choice(["growth", "finance", "regional_marketing"]),
                            }
                        )
                        if len(records) >= rows:
                            return pd.DataFrame(records)
        return pd.DataFrame(records)

    def _event_dates(self, rows: int) -> pd.DatetimeIndex:
        weights = np.array([self._month_weight(date.month) for date in self.date_range], dtype=float)
        weights = weights / weights.sum()
        indexes = self.rng.choice(len(self.date_range), size=rows, p=weights)
        return pd.DatetimeIndex(self.date_range[indexes])

    def _month_weight(self, month: int) -> float:
        return {
            1: 0.9,
            2: 0.92,
            3: 1.02,
            4: 1.03,
            5: 1.08,
            6: 1.12,
            7: 0.98,
            8: 1.02,
            9: 1.15,
            10: 1.28,
            11: 1.65,
            12: 1.78,
        }[month]

    def _seasonality(self, dates: pd.DatetimeIndex) -> np.ndarray:
        return np.array([self._month_weight(date.month) for date in dates])

    def _campaign_ids(self, rows: int, missing_rate: float = 0.0) -> np.ndarray:
        pool = max(50, min(50000, rows // 30 + 50))
        values = np.array([f"CMP-{value:06d}" for value in self.rng.integers(1, pool + 1, rows)], dtype=object)
        if missing_rate:
            values[self.rng.random(rows) < missing_rate] = None
        return values

    def _campaign_names(self, rows: int, social: bool = False) -> np.ndarray:
        base = self.rng.choice(self.campaign_templates, rows)
        year = self.rng.choice(["2024", "2025", "FY25", "Q4"], rows)
        region = self.rng.choice(["US", "NA", "EMEA", "APAC", "Global"], rows)
        variants = []
        for template, year_value, region_value in zip(base, year, region, strict=False):
            name = f"{template} {region_value} {year_value}"
            style = self.rng.choice(["title", "snake", "upper", "extra_space", "legacy"])
            if social:
                name = f"{name} Social"
            if style == "snake":
                name = name.lower().replace(" ", "_")
            elif style == "upper":
                name = name.upper()
            elif style == "extra_space":
                name = f" {name}  "
            elif style == "legacy":
                name = name.replace("Search", "SEM").replace("Promo", "Promotion")
            variants.append(name)
        return np.array(variants, dtype=object)

    def _attribution_ids(self, rows: int, missing_rate: float) -> np.ndarray:
        ids = np.array(
            [f"ATTR-{value:012d}" for value in self.rng.integers(1, self.attribution_pool_size, rows)],
            dtype=object,
        )
        ids[self.rng.random(rows) < missing_rate] = None
        return ids

    def _updated_at(self, dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
        normal_delay = self.rng.integers(0, 4, len(dates))
        late_delay = self.rng.integers(30, 91, len(dates))
        is_late = self.rng.random(len(dates)) < 0.055
        delay = np.where(is_late, late_delay, normal_delay)
        return pd.to_datetime(dates) + pd.to_timedelta(delay, unit="D")

    def _inject_paid_media_defects(self, frame: pd.DataFrame, spend_column: str) -> pd.DataFrame:
        rows = len(frame)
        frame.loc[self.rng.random(rows) < 0.006, spend_column] = np.nan
        denominator_column = "impressions" if "impressions" in frame.columns else "video_views"
        frame.loc[self.rng.random(rows) < 0.002, "clicks"] = frame[denominator_column].fillna(0) + 10
        if rows > 10:
            duplicate_sample = frame.sample(frac=0.004, random_state=int(self.rng.integers(1, 999999)))
            frame = pd.concat([frame, duplicate_sample], ignore_index=True)
        return frame


def safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(numerator, denominator, out=np.zeros_like(numerator, dtype=float), where=denominator != 0).round(6)


def manifest_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def write_partition(
    frame: pd.DataFrame,
    output_dir: Path,
    source_system: str,
    chunk_number: int,
    preferred_format: str,
) -> tuple[Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fmt = preferred_format.lower()
    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401

            path = output_dir / f"{source_system}_part_{chunk_number:05d}.parquet"
            frame.to_parquet(path, index=False)
            return path, "parquet"
        except Exception:
            fmt = "csv"
    if fmt in {"json", "jsonl"}:
        path = output_dir / f"{source_system}_part_{chunk_number:05d}.jsonl"
        frame.to_json(path, orient="records", lines=True, date_format="iso")
        return path, "jsonl"
    path = output_dir / f"{source_system}_part_{chunk_number:05d}.csv"
    frame.to_csv(path, index=False)
    return path, "csv"


def load_profile(config_path: Path, profile: str) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if profile not in config["profiles"]:
        available = ", ".join(sorted(config["profiles"]))
        raise ValueError(f"Unknown profile {profile!r}. Available profiles: {available}")
    profile_config = dict(config["profiles"][profile])
    profile_config["formats"] = config.get("formats", {})
    return profile_config


def run_generation(profile: str, config_path: Path = DEFAULT_CONFIG, clean: bool = True) -> GenerationManifest:
    profile_config = load_profile(config_path, profile)
    generator = SyntheticMarketingGenerator(
        start_date=profile_config["start_date"],
        end_date=profile_config["end_date"],
        output_root=profile_config["output_root"],
    )
    return generator.generate_all(
        profile=profile,
        row_counts=profile_config["row_counts"],
        formats=profile_config["formats"],
        chunk_size=int(profile_config["chunk_size"]),
        clean=clean,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic multi-source marketing datasets.")
    parser.add_argument("--profile", default="dev", help="Profile name from config/source_volume.yml.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to source volume config.")
    parser.add_argument("--no-clean", action="store_true", help="Append a new generated batch instead of cleaning output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_generation(profile=args.profile, config_path=Path(args.config), clean=not args.no_clean)
    print(json.dumps(manifest.to_dict(), indent=2))


if __name__ == "__main__":
    main()
