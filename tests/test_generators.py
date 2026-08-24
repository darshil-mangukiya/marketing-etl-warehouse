from pathlib import Path

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
