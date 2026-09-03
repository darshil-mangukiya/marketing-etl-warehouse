from __future__ import annotations

import json
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "executive_review" / "Marketing_Monthly_Business_Review.pptx"
METRICS = ROOT / "executive_review" / "data" / "deck_metrics.json"
REPORT = ROOT / "executive_review" / "validation_report.json"
RENDER_DIR = Path(tempfile.gettempdir()) / "p2_marketing_mbr_rendered"

EXPECTED_TITLES = [
    "Review first.",
    "Validate the signal before changing budget",
    "The scorecard says review, not scale",
    "Weak return is not isolated to one campaign",
    "Paid social loses most volume before MQL",
    "Attribution changes magnitude—not the leader",
    "Near-plan spend masks conflicting signals",
    "All simulated cases stay below 1.0x ROAS",
    "Source failures require a manual release hold",
    "Resolve trust first, then review performance",
]

FORBIDDEN_PATTERNS = {
    "personal_path": re.compile(r"/Users/darshil/|file://", re.IGNORECASE),
    "ai_residue": re.compile(r"\b(?:ChatGPT|Codex|OpenAI|AI generated)\b", re.IGNORECASE),
    "placeholder": re.compile(r"\b(?:Lorem ipsum|placeholder text|TBD|TODO|FIXME)\b", re.IGNORECASE),
    "secret": re.compile(r"(?:sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=]|password\s*[:=]|BEGIN PRIVATE KEY)", re.IGNORECASE),
    "unsupported_claim": re.compile(
        r"\b(?:actual executive approval|actual stakeholder adoption|realized revenue impact|realized savings|production-scale 38M|enterprise SLA ownership)\b",
        re.IGNORECASE,
    ),
}


TEXT_NAMESPACE = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def part_number(name: str) -> int:
    match = re.search(r"(\d+)\.xml$", name)
    if not match:
        raise ValueError(f"Office part has no numeric suffix: {name}")
    return int(match.group(1))


def part_text(archive: zipfile.ZipFile, name: str) -> str:
    root = ET.fromstring(archive.read(name))
    return "\n".join(node.text or "" for node in root.findall(".//a:t", TEXT_NAMESPACE))


def main() -> None:
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    checks["pptx_exists"] = DECK.exists() and DECK.stat().st_size > 0
    checks["valid_office_archive"] = zipfile.is_zipfile(DECK)
    archive_names: list[str] = []
    external_targets: list[str] = []
    texts: list[str] = []
    notes: list[str] = []
    office_xml = ""
    if checks["valid_office_archive"]:
        with zipfile.ZipFile(DECK) as archive:
            archive_names = archive.namelist()
            checks["required_office_parts"] = all(
                part in archive_names for part in ("[Content_Types].xml", "ppt/presentation.xml")
            )
            for name in archive_names:
                if name.endswith(".rels"):
                    text = archive.read(name).decode("utf-8", errors="ignore")
                    external_targets.extend(
                        re.findall(r'Target="([^"]+)"[^>]*TargetMode="External"', text)
                    )
            slide_parts = sorted(
                (
                    name
                    for name in archive_names
                    if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
                ),
                key=part_number,
            )
            note_parts = sorted(
                (
                    name
                    for name in archive_names
                    if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
                ),
                key=part_number,
            )
            texts = [part_text(archive, name) for name in slide_parts]
            notes = [part_text(archive, name) for name in note_parts]
            office_xml = "\n".join(
                archive.read(name).decode("utf-8", errors="ignore")
                for name in archive_names
                if name.endswith((".xml", ".rels"))
            )
    else:
        checks["required_office_parts"] = False
    combined = "\n".join(texts + notes + [office_xml])

    checks["expected_slide_count"] = len(texts) == 10
    checks["expected_notes_count"] = len(notes) == 10
    checks["no_empty_slides"] = all(text.strip() for text in texts)
    checks["slide_titles_present"] = all(
        expected in text for expected, text in zip(EXPECTED_TITLES, texts, strict=True)
    )
    checks["sources_in_every_slide_notes"] = all("[Sources]" in note for note in notes)
    checks["no_broken_local_paths"] = not any(
        target.startswith(("file:", "/", "../")) for target in external_targets
    )
    checks["regular_footer_exact"] = all(
        f"MODELED PORTFOLIO CASE STUDY   {number}" in texts[number - 1]
        for number in range(2, 11)
    )
    checks["legacy_footer_absent"] = (
        "GENERATED BUSINESS DATA · MODELED PORTFOLIO CASE STUDY" not in combined
    )
    checks["synthetic_boundary_present"] = (
        "GENERATED / SYNTHETIC MARKETING DATA" in texts[0]
        and "SIMULATED / WHAT-IF" in combined
    )

    pattern_hits: dict[str, list[str]] = {}
    for name, pattern in FORBIDDEN_PATTERNS.items():
        hits = sorted(set(match.group(0) for match in pattern.finditer(combined)))
        pattern_hits[name] = hits
        checks[f"no_{name}"] = not hits

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))["summaries"]
    expected_metric_strings = {
        "paid_social_roas": f'{metrics["REQ-01"]["channel_roas"]:.2f}x',
        "paid_social_spend": f'${metrics["REQ-01"]["total_spend"] / 1_000_000:.2f}M',
        "paid_social_revenue": f'${round(metrics["REQ-01"]["total_revenue"] / 1000)}K',
        "lead_to_mql_leakage": f'{metrics["REQ-02"]["leakage_rate"]:.0%}',
        "expected_scenario_roas": f'{metrics["REQ-05"]["expected_roas"]:.2f}x',
        "quality_failures": str(metrics["REQ-06"]["quality_failures"]),
        "campaign_action_holds": str(metrics["REQ-06"]["campaign_action_holds"]),
    }
    checks["metrics_trace_to_source"] = all(value in combined for value in expected_metric_strings.values())

    render_pngs = sorted(RENDER_DIR.glob("slide-*.png"))
    layout_paths = sorted(RENDER_DIR.glob("slide-*.layout.json"))
    checks["artifact_render_set_present"] = len(render_pngs) == 10 and all(
        path.stat().st_size > 0 for path in render_pngs
    )
    bounds_pass = len(layout_paths) == 10
    for path in layout_paths:
        layout = json.loads(path.read_text(encoding="utf-8"))
        frame = layout["slide"]["frame"]
        slide_width = float(frame["width"])
        slide_height = float(frame["height"])
        for element in layout.get("elements", []):
            bbox = element.get("bbox")
            if not bbox:
                continue
            left, top, width, height = map(float, bbox)
            if not (
                left >= 0
                and top >= 0
                and width > 0
                and height > 0
                and left + width <= slide_width + 0.5
                and top + height <= slide_height + 0.5
            ):
                bounds_pass = False
    checks["artifact_layout_bounds_pass"] = bounds_pass

    details["slide_count"] = len(texts)
    details["slide_titles"] = [text.splitlines()[0] for text in texts]
    details["external_relationship_targets"] = external_targets
    details["forbidden_pattern_hits"] = pattern_hits
    details["expected_metric_strings"] = expected_metric_strings
    details["archive_part_count"] = len(archive_names)
    details["visual_validation"] = {
        "artifact_renderer": "10_slide_pngs_generated_and_inspected",
        "artifact_layout_bounds": "all_element_bboxes_within_slide_canvas",
        "office_compatible_renderer": "not_available_in_current_sandbox",
        "manual_powerpoint_review": "recommended_after_local_handoff",
    }
    details["evidence_boundary"] = (
        "Generated marketing business data; bounded real portfolio-site GA4 remains separate and unused."
    )

    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "deck": "executive_review/Marketing_Monthly_Business_Review.pptx",
        "checks": checks,
        "details": details,
    }
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
