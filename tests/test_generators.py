from pathlib import Path

import pandas as pd

from data_sources.generators import SyntheticMarketingGenerator


def test_generator_writes_manifest_and_partitioned_sources(tmp_path: Path) -> None:
    generator = SyntheticMarketingGenerator("2025-01-01", "2025-01-05", tmp_path, seed=7)
    manifest = generator.generate_all(
        profile="unit",
        row_counts={
            "google_ads": 25,
            "facebook_ads": 20,
            "tiktok_ads": 15,
            "website_analytics": 30,
            "crm_leads": 25,
            "sales_conversions": 10,
            "marketing_targets": 8,
        },
        formats={
            "google_ads": "jsonl",
            "facebook_ads": "csv",
            "tiktok_ads": "csv",
            "website_analytics": "csv",
            "crm_leads": "csv",
            "sales_conversions": "jsonl",
            "marketing_targets": "csv",
        },
        chunk_size=10,
    )

    assert manifest.batch_id.startswith("batch_")
    assert (tmp_path / "manifest.json").exists()
    assert len(manifest.parts) >= 7
    assert all((Path(__file__).resolve().parents[1] / part.path).exists() for part in manifest.parts)


def test_sales_conversions_link_to_generated_lead_cohorts(tmp_path: Path) -> None:
    generator = SyntheticMarketingGenerator("2025-01-01", "2025-01-31", tmp_path, seed=17)
    leads = generator.crm_leads(500)
    conversions = generator.sales_conversions(300)

    active_leads = leads[leads["cdc_operation"].ne("D")].drop_duplicates("lead_id", keep="last")
    sql_ids = set(active_leads.loc[active_leads["qualification_stage"].eq("sales_qualified"), "lead_id"])
    converted_sql_ids = set(conversions["lead_id"]) & sql_ids

    assert converted_sql_ids
    assert len(converted_sql_ids) <= len(sql_ids)
    linked = conversions[conversions["lead_id"].isin(active_leads["lead_id"])].merge(
        active_leads[["lead_id", "created_at"]], on="lead_id", suffixes=("_conversion", "_lead")
    )
    assert (pd.to_datetime(linked["conversion_date"]) >= pd.to_datetime(linked["created_at_lead"])).all()
