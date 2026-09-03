from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "analytics_requests"
DECK = ROOT / "executive_review" / "Marketing_Monthly_Business_Review.pptx"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_request_manifest_defines_six_modeled_requests() -> None:
    manifest = yaml.safe_load((PACK / "manifest.yml").read_text(encoding="utf-8"))
    requests = manifest["requests"]
    assert [request["id"] for request in requests] == [f"REQ-{index:02d}" for index in range(1, 7)]
    assert manifest["portfolio_case_study"] is True
    assert manifest["build"]["request_count"] == 6
    assert all(request["requester"] for request in requests)


def test_request_results_and_validations_are_non_empty_and_traceable() -> None:
    manifest = yaml.safe_load((PACK / "manifest.yml").read_text(encoding="utf-8"))
    for request in manifest["requests"]:
        directory = PACK / request["slug"]
        result = directory / "result.csv"
        validation = json.loads((directory / "validation.json").read_text(encoding="utf-8"))
        assert result.exists() and result.stat().st_size > 0
        with result.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert validation["status"] == "PASS"
        assert validation["result_rows"] == len(rows)
        assert validation["result_sha256"] == digest(result)
        assert all(item["path"] and item["sha256"] for item in validation["inputs"])


def test_each_request_has_complete_storytelling_contract() -> None:
    required = [
        "## 4. Clarifying questions",
        "## 6. Data sources / marts used",
        "## 9. Validation / reconciliation checks",
        "## 12. What happened? — OBSERVATION",
        "## 13. Why did it happen? — INTERPRETATION",
        "## 14. So what? — BUSINESS INTERPRETATION",
        "## 15. Recommended action — HUMAN REVIEW REQUIRED",
        "## 16. Risks / caveats",
        "## 18. Final concise stakeholder response",
    ]
    for directory in sorted(PACK.glob("request_*")):
        text = (directory / "request.md").read_text(encoding="utf-8")
        assert all(section in text for section in required)
        assert "Modeled stakeholder request" in text or "modeled stakeholder request" in text
        assert (directory / "analysis.sql").exists()
        assert (directory / "response_memo.md").exists()


def test_request_charts_are_valid_non_empty_pngs() -> None:
    for path in sorted(PACK.glob("request_*/chart.png")):
        data = path.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        assert width >= 1000 and height >= 500


def test_modeled_stakeholder_logs_cover_the_six_requests() -> None:
    log_dir = ROOT / "business_analysis" / "stakeholder_requests"
    for filename in ("stakeholder_request_log.csv", "decision_log.csv", "action_tracker.csv"):
        with (log_dir / filename).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 6
        assert {row["request_id"] for row in rows} == {f"REQ-{index:02d}" for index in range(1, 7)}
        assert all("case study" in row["scenario_type"] or "modeled" in row["scenario_type"] or "simulated" in row["scenario_type"] for row in rows)


def test_powerpoint_archive_has_ten_titled_sourced_slides() -> None:
    assert zipfile.is_zipfile(DECK)
    with zipfile.ZipFile(DECK) as archive:
        slide_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda name: int(re.search(r"(\d+)\.xml$", name).group(1)),
        )
        note_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)),
            key=lambda name: int(re.search(r"(\d+)\.xml$", name).group(1)),
        )
        assert len(slide_names) == 10
        assert len(note_names) == 10
        namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        slide_texts = []
        for name in slide_names:
            root = ET.fromstring(archive.read(name))
            text = " ".join(node.text or "" for node in root.findall(".//a:t", namespace))
            slide_texts.append(text)
            assert text.strip()
        for name in note_names:
            root = ET.fromstring(archive.read(name))
            text = " ".join(node.text or "" for node in root.findall(".//a:t", namespace))
            assert "[Sources]" in text
        office_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith((".xml", ".rels"))
        )
    assert any("Attribution changes magnitude" in text for text in slide_texts)
    assert any("DATA QUALITY HOLD" in text for text in slide_texts)
    assert all(
        f"MODELED PORTFOLIO CASE STUDY   {number}" in slide_texts[number - 1]
        for number in range(2, 11)
    )
    assert "GENERATED / SYNTHETIC MARKETING DATA" in slide_texts[0]
    assert "GENERATED BUSINESS DATA · MODELED PORTFOLIO CASE STUDY" not in office_xml
    assert not re.search(
        r"\b(?:ChatGPT|Codex|OpenAI)\b|/Users/darshil/|file://",
        office_xml,
        re.IGNORECASE,
    )


def test_published_upgrade_artifacts_are_public_safe() -> None:
    roots = [PACK, ROOT / "executive_review", ROOT / "business_analysis" / "stakeholder_requests", ROOT / "docs" / "career"]
    forbidden = re.compile(
        r"/Users/darshil/|file://|\b(?:ChatGPT|Codex|AI generated|Lorem ipsum|TODO|FIXME)\b|sk-[A-Za-z0-9]{16,}|BEGIN PRIVATE KEY",
        re.IGNORECASE,
    )
    text_suffixes = {".md", ".csv", ".json", ".yml", ".yaml", ".sql", ".py", ".mjs"}
    for root in roots:
        for path in root.rglob("*"):
            if path.name in {"validate_deck.py"}:
                continue
            if path.is_file() and path.suffix.lower() in text_suffixes:
                assert not forbidden.search(path.read_text(encoding="utf-8")), path


def test_recruiter_first_links_resolve() -> None:
    expected = [
        ROOT / "executive_review" / "Marketing_Monthly_Business_Review.pptx",
        ROOT / "analytics_requests" / "README.md",
        ROOT / "evidence" / "screenshots" / "powerbi" / "executive_overview.png",
        ROOT / "evidence" / "generated" / "architecture_snapshot.svg",
        ROOT / "docs" / "career" / "P2_RECRUITER_BRIEF.md",
        ROOT / "docs" / "career" / "P2_INTERVIEW_GUIDE.md",
    ]
    assert all(path.exists() for path in expected)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert all(path.relative_to(ROOT).as_posix() in readme for path in expected[4:])


def test_req04_attribution_leader_is_consistent_across_publication_artifacts() -> None:
    request_dir = PACK / "request_04_attribution_sensitivity"
    with (request_dir / "result.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    method_stems = (
        "first_touch",
        "last_touch",
        "linear",
        "u_shaped",
        "time_decay",
        "position_based",
    )
    assert len(method_stems) == 6
    leaders: dict[str, str] = {}
    for stem in method_stems:
        revenue_column = f"{stem}_revenue"
        rank_column = f"{stem}_rank"
        assert all(revenue_column in row and rank_column in row for row in rows)
        rank_one = [row for row in rows if int(row[rank_column]) == 1]
        assert len(rank_one) == 1
        assert float(rank_one[0][revenue_column]) == max(float(row[revenue_column]) for row in rows)
        leaders[stem] = rank_one[0]["channel_name"]

    assert len(set(leaders.values())) == 1
    actual_leader = next(iter(leaders.values()))
    leader_row = next(row for row in rows if row["channel_name"] == actual_leader)

    manifest = yaml.safe_load((PACK / "manifest.yml").read_text(encoding="utf-8"))
    summary = manifest["summaries"]["REQ-04"]
    assert summary["top_channel"] == actual_leader
    assert summary["rank_stable"] is True
    assert actual_leader in summary["chart_title"]
    assert abs(summary["min_revenue"] - float(leader_row["min_attributed_revenue"])) < 1e-9
    assert abs(summary["max_revenue"] - float(leader_row["max_attributed_revenue"])) < 1e-9
    assert abs(summary["spread_pct"] - float(leader_row["model_spread_pct"])) < 1e-6

    deck_metrics = json.loads(
        (ROOT / "executive_review" / "data" / "deck_metrics.json").read_text(encoding="utf-8")
    )
    assert deck_metrics["summaries"]["REQ-04"]["top_channel"] == actual_leader

    publication_texts = {
        "request": (request_dir / "request.md").read_text(encoding="utf-8"),
        "memo": (request_dir / "response_memo.md").read_text(encoding="utf-8"),
        "executive_brief": (ROOT / "executive_review" / "EXECUTIVE_ANALYTICS_BRIEF.md").read_text(encoding="utf-8"),
        "decision_log": (ROOT / "business_analysis" / "stakeholder_requests" / "decision_log.csv").read_text(encoding="utf-8"),
        "action_tracker": (ROOT / "business_analysis" / "stakeholder_requests" / "action_tracker.csv").read_text(encoding="utf-8"),
    }
    assert f"{actual_leader} ranks first under all six attribution methods" in publication_texts["request"]
    assert f"{actual_leader} ranks first under all six attribution methods" in publication_texts["memo"]
    assert f"{actual_leader} ranks first under all six attribution methods" in publication_texts["executive_brief"]
    assert actual_leader in publication_texts["decision_log"]
    assert actual_leader in publication_texts["action_tracker"]

    interview = (ROOT / "docs" / "career" / "P2_INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    if "REQ-04" in interview:
        assert actual_leader in interview

    validation = json.loads((request_dir / "validation.json").read_text(encoding="utf-8"))
    assert validation["checks"]["summary_channel_is_rank_one"] is True

    with zipfile.ZipFile(DECK) as archive:
        deck_text = " ".join(
            node.text or ""
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            for node in ET.fromstring(archive.read(name)).iter()
            if node.tag.endswith("}t")
        )
    assert f"{actual_leader} ranks first under all six methods" in deck_text

    for row in rows:
        other_channel = row["channel_name"]
        if other_channel == actual_leader:
            continue
        assert all(
            f"{other_channel} ranks first under all six attribution methods" not in text
            for text in publication_texts.values()
        )
        assert f"{other_channel} ranks first under all six methods" not in deck_text


def test_analysis_pack_is_deterministic_and_cross_artifact_facts_agree() -> None:
    tracked = sorted(
        path
        for path in PACK.rglob("*")
        if path.is_file() and path.name not in {"build_analysis_pack.py"}
    ) + [ROOT / "executive_review" / "data" / "deck_metrics.json"]
    first_build: dict[Path, str] | None = None
    for _ in range(2):
        subprocess.run(
            ["python3", "-B", "analytics_requests/build_analysis_pack.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        current = {path: digest(path) for path in tracked}
        if first_build is not None:
            assert current == first_build
        first_build = current

    manifest = yaml.safe_load((PACK / "manifest.yml").read_text(encoding="utf-8"))
    summary = manifest["summaries"]["REQ-03"]
    request_log = (ROOT / "business_analysis" / "stakeholder_requests" / "stakeholder_request_log.csv").read_text(encoding="utf-8")
    interview = (ROOT / "docs" / "career" / "P2_INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    quality_request = (PACK / "request_06_data_quality_investigation" / "request.md").read_text(encoding="utf-8")
    assert summary["region"] in request_log
    assert f'{manifest["summaries"]["REQ-01"]["top_two_share"]:.1%}' in interview
    assert "quality_failure status" in quality_request
    assert "freshness_failure status" not in quality_request
