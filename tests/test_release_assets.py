import json
from pathlib import Path

import scripts.build_release_site as release_site
import scripts.generate_release_bundle as release_bundle


def test_release_bundle_manifest_is_generated(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "release" / "generated"
    monkeypatch.setattr(release_bundle, "OUTPUT_DIR", output_dir)

    manifest = release_bundle.generate_release_bundle()

    assert manifest["artifact_count"] == len(release_bundle.ARTIFACTS)
    assert "recommended_review_order" in manifest
    assert (output_dir / "release_manifest.json").exists()
    assert (output_dir / "release_index.html").exists()


def test_powerbi_pbip_scaffold_is_valid_json() -> None:
    pbip = json.loads(Path("semantic_layer/powerbi_pbip/MarketingPlatform.pbip").read_text(encoding="utf-8"))
    report = json.loads(Path("semantic_layer/powerbi_pbip/definition/report.json").read_text(encoding="utf-8"))
    pages = json.loads(Path("semantic_layer/powerbi_pbip/definition/pages.json").read_text(encoding="utf-8"))

    assert pbip["settings"]["sourceControlFriendly"] is True
    assert report["expectedSemanticSource"] == "../powerbi_tmdl"
    assert len(pages["pages"]) >= 6


def test_github_workflows_exist_without_push_side_effects() -> None:
    workflow_dir = Path(".github/workflows")
    workflows = {path.name for path in workflow_dir.glob("*.yml")}

    assert workflows == {"local-quality-gate.yml"}

    workflow_text = (workflow_dir / "local-quality-gate.yml").read_text(encoding="utf-8")
    declared_name = next(
        line.partition(":")[2].strip() for line in workflow_text.splitlines() if line.startswith("name:")
    )

    assert declared_name == "Local Quality Gate"
    for side_effect in ("git push", "docker push", "gh release", "actions/deploy-pages"):
        assert side_effect not in workflow_text


def test_streamlit_screenshots_are_published_in_release_site(tmp_path, monkeypatch) -> None:
    site_dir = tmp_path / "release" / "site"
    monkeypatch.setattr(release_site, "SITE_DIR", site_dir)

    manifest = release_site.build_release_site()
    screenshots = manifest["streamlit_screenshots"]

    assert len(screenshots) == 9
    assert all((site_dir / path).exists() for path in screenshots.values())

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Streamlit Dashboard Screenshots" in index
    assert "Executive Overview Screenshot" in index
    assert "Channel Performance Screenshot" in index
    assert "Data Quality Screenshot" in index
