from scripts.generate_lineage_metadata import build_datahub_mces, build_openlineage_events
from scripts.generate_powerbi_semantic_model import build_model_tmdl, semantic_model_spec


def test_powerbi_semantic_spec_has_expected_pages_and_measures():
    spec = semantic_model_spec()
    page_names = {page["page"] for page in spec["dashboard_pages"]}
    measure_count = sum(len(table.get("measures", [])) for table in spec["tables"])

    assert "Executive Marketing Overview" in page_names
    assert "Attribution & ROI" in page_names
    assert measure_count >= 25
    assert "discourageImplicitMeasures" in build_model_tmdl(spec)


def test_lineage_metadata_builds_openlineage_and_datahub_payloads():
    catalog = {
        "models": [
            {"name": "stg_google_ads", "layer": "staging", "refs": [], "sources": ["raw.google_ads"]},
            {"name": "mart_channel_performance", "layer": "reporting", "refs": ["stg_google_ads"], "sources": []},
        ],
        "semantic_assets": [{"asset_type": "exposure", "name": "executive_marketing_overview"}],
    }

    openlineage_events = build_openlineage_events(catalog)
    datahub_mces = build_datahub_mces(catalog)

    assert len(openlineage_events) == 2
    assert any(event["outputs"][0]["name"] == "mart_channel_performance" for event in openlineage_events)
    assert any(event["entityType"] == "dashboard" for event in datahub_mces)
