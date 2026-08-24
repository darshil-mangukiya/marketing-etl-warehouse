from __future__ import annotations

import html
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = PROJECT_ROOT / "release" / "site"


def _load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_file(source: Path, destination: Path) -> str | None:
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(destination.relative_to(SITE_DIR))


def build_release_site() -> dict:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    asset_dir = SITE_DIR / "assets"
    report_dir = SITE_DIR / "reports"
    monitoring_dir = SITE_DIR / "monitoring"
    docs_dir = SITE_DIR / "docs"
    data_dir = SITE_DIR / "data"
    screenshot_dir = SITE_DIR / "screenshots" / "streamlit"

    release_manifest = _load_json(PROJECT_ROOT / "release" / "generated" / "release_manifest.json")
    quality_gate = _load_json(PROJECT_ROOT / "local_ci" / "latest_quality_gate.json")
    semantic_manifest = _load_json(PROJECT_ROOT / "semantic_layer" / "powerbi_tmdl" / "semantic_model_manifest.json")
    governance_manifest = _load_json(PROJECT_ROOT / "governance" / "generated" / "governance_manifest.json")

    copied_assets = []
    for source in sorted((PROJECT_ROOT / "evidence" / "generated").glob("*.svg")):
        copied = _copy_file(source, asset_dir / source.name)
        if copied:
            copied_assets.append(copied)

    report_sources = [
        PROJECT_ROOT / "reports" / "generated" / "executive_marketing_report.html",
        PROJECT_ROOT / "reports" / "generated" / "executive_planning_report.html",
        PROJECT_ROOT / "reports" / "generated" / "governance_release_packet.html",
    ]
    copied_reports = [
        copied
        for source in report_sources
        if (copied := _copy_file(source, report_dir / source.name))
    ]

    copied_monitoring = _copy_file(
        PROJECT_ROOT / "monitoring" / "generated" / "observability_dashboard.html",
        monitoring_dir / "observability_dashboard.html",
    )
    screenshot_sources = {
        "Executive Overview Screenshot": "executive_overview.png",
        "Channel Performance Screenshot": "channel_performance.png",
        "Campaign Intelligence Screenshot": "campaign_intelligence.png",
        "Funnel Analysis Screenshot": "funnel_analysis.png",
        "Attribution and ROI Screenshot": "attribution_roi.png",
        "Target vs Actual Screenshot": "target_vs_actual.png",
        "Data Quality Screenshot": "data_quality_monitoring.png",
        "Customer Value Screenshot": "customer_value.png",
        "Source Health Screenshot": "source_health.png",
    }
    copied_screenshots = {
        label: copied
        for label, filename in screenshot_sources.items()
        if (
            copied := _copy_file(
                PROJECT_ROOT / "evidence" / "screenshots" / "streamlit" / filename,
                screenshot_dir / filename,
            )
        )
    }
    copied_data = [
        _copy_file(PROJECT_ROOT / "release" / "generated" / "release_manifest.json", data_dir / "release_manifest.json"),
        _copy_file(PROJECT_ROOT / "local_ci" / "latest_quality_gate.json", data_dir / "latest_quality_gate.json"),
        _copy_file(PROJECT_ROOT / "data" / "exports" / "demo_mart_manifest.json", data_dir / "demo_mart_manifest.json"),
    ]

    technical_doc_sources = {
        "Execution Profiles": PROJECT_ROOT / "docs" / "execution_profiles.md",
        "Row Count Summary": PROJECT_ROOT / "docs" / "row_count_summary.md",
        "Incremental Loading": PROJECT_ROOT / "docs" / "incremental_load_evidence.md",
        "Data Quality Framework": PROJECT_ROOT / "docs" / "data_quality_framework.md",
        "Warehouse Model": PROJECT_ROOT / "docs" / "warehouse_model.md",
        "Dashboard Outputs": PROJECT_ROOT / "docs" / "dashboard_outputs.md",
        "Business Requirements": PROJECT_ROOT / "docs" / "business_requirements.md",
        "Stakeholder Map": PROJECT_ROOT / "docs" / "stakeholder_map.md",
        "User Stories and Acceptance Criteria": PROJECT_ROOT / "docs" / "user_stories_acceptance_criteria.md",
        "UAT Checklist": PROJECT_ROOT / "docs" / "uat_checklist.md",
        "Dashboard Requirements": PROJECT_ROOT / "docs" / "dashboard_requirements.md",
        "Business Insights and Recommendations": PROJECT_ROOT / "docs" / "business_insights_and_recommendations.md",
        "Business Decision Workflow": PROJECT_ROOT / "docs" / "business_decision_workflow.md",
        "Power BI Setup Guide": PROJECT_ROOT / "semantic_layer" / "powerbi" / "POWERBI_SETUP_GUIDE.md",
        "Power BI Assets": PROJECT_ROOT / "semantic_layer" / "powerbi" / "POWERBI_EVIDENCE.md",
        "Excel-ready Analysis": PROJECT_ROOT / "reports" / "generated" / "excel_ready" / "README.md",
    }
    copied_docs = {}
    for label, source in technical_doc_sources.items():
        destination_name = "excel_ready_analysis.md" if label == "Excel-ready Analysis" else source.name
        copied = _copy_file(source, docs_dir / destination_name)
        if copied:
            copied_docs[label] = copied

    include_dbt_docs = os.getenv("INCLUDE_DBT_DOCS", "0").lower() in {"1", "true", "yes"}
    dbt_docs_source = PROJECT_ROOT / "dbt" / "target" / "static_index.html"
    copied_dbt_docs = (
        _copy_file(dbt_docs_source, docs_dir / "dbt_static_index.html")
        if include_dbt_docs
        else None
    )

    index_html = _render_index(
        release_manifest=release_manifest,
        quality_gate=quality_gate,
        semantic_manifest=semantic_manifest,
        governance_manifest=governance_manifest,
        copied_dbt_docs=copied_dbt_docs,
        copied_monitoring=copied_monitoring,
        copied_docs=copied_docs,
        copied_screenshots=copied_screenshots,
    )
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    try:
        site_dir = str(SITE_DIR.relative_to(PROJECT_ROOT))
    except ValueError:
        site_dir = str(SITE_DIR)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_dir": site_dir,
        "status": "generated",
        "assets": copied_assets,
        "reports": copied_reports,
        "monitoring": copied_monitoring,
        "dbt_docs": copied_dbt_docs,
        "technical_docs": copied_docs,
        "streamlit_screenshots": copied_screenshots,
        "data": [item for item in copied_data if item],
    }
    (SITE_DIR / "site_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _render_index(
    release_manifest: dict,
    quality_gate: dict,
    semantic_manifest: dict,
    governance_manifest: dict,
    copied_dbt_docs: str | None,
    copied_monitoring: str | None,
    copied_docs: dict[str, str],
    copied_screenshots: dict[str, str],
) -> str:
    artifacts = [
        artifact
        for artifact in release_manifest.get("artifacts", [])
        if "case_study" not in artifact.get("path", "")
    ]
    artifact_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(artifact.get('name', ''))}</td>"
        f"<td><code>{html.escape(artifact.get('path', ''))}</code></td>"
        f"<td>{'available' if artifact.get('exists') else 'missing'}</td>"
        "</tr>"
        for artifact in artifacts
    )
    doc_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(label)}</td>"
        f"<td><a href=\"{html.escape(path)}\">{html.escape(path)}</a></td>"
        "</tr>"
        for label, path in copied_docs.items()
    )
    screenshot_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(label)}</td>"
        f'<td><a href="{html.escape(path)}">{html.escape(path)}</a></td>'
        "</tr>"
        for label, path in copied_screenshots.items()
    )
    featured_screenshot_labels = [
        "Executive Overview Screenshot",
        "Channel Performance Screenshot",
        "Data Quality Screenshot",
    ]
    featured_screenshots = "\n".join(
        f'<a href="{html.escape(copied_screenshots[label])}">'
        f'<img src="{html.escape(copied_screenshots[label])}" alt="{html.escape(label)}"></a>'
        for label in featured_screenshot_labels
        if label in copied_screenshots
    )
    quality_status = quality_gate.get("status", "unknown")
    checks = quality_gate.get("checks", [])
    passed_checks = sum(1 for check in checks if check.get("return_code") == 0)
    table_count = semantic_manifest.get("table_count", len(semantic_manifest.get("tables", [])))
    measure_count = semantic_manifest.get("measure_count", 0)
    governance_status = governance_manifest.get("status", "generated")
    dbt_link = f'<a href="{html.escape(copied_dbt_docs)}">Open static dbt docs</a>' if copied_dbt_docs else "Generate dbt docs to enable this link."
    monitoring_link = (
        f'<a href="{html.escape(copied_monitoring)}">Open observability dashboard</a>'
        if copied_monitoring
        else "Observability dashboard has not been generated."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Marketing Data Platform</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #5b677a;
      --line: #d8dee8;
      --blue: #2563eb;
      --paper: #ffffff;
      --wash: #f6f8fb;
    }}
    body {{ margin: 0; font-family: Arial, sans-serif; color: var(--ink); background: var(--wash); line-height: 1.55; }}
    header {{ background: #111827; color: white; padding: 44px 5vw; }}
    header h1 {{ margin: 0 0 8px; font-size: 38px; }}
    header p {{ max-width: 980px; color: #d1d5db; margin: 0; font-size: 17px; }}
    main {{ width: min(1180px, 90vw); margin: 34px auto 70px; }}
    section {{ background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 26px; margin-bottom: 24px; }}
    h2 {{ margin: 0 0 14px; font-size: 24px; }}
    h3 {{ margin: 22px 0 8px; font-size: 18px; }}
    ul {{ margin: 10px 0 0 20px; padding: 0; }}
    li {{ margin: 6px 0; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }}
    .metric {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fbfdff; }}
    .metric span {{ color: var(--muted); display: block; font-size: 13px; margin-bottom: 8px; }}
    .metric strong {{ font-size: 24px; }}
    .visual-grid {{ display: grid; grid-template-columns: 1fr; gap: 18px; }}
    .two-col {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .callout {{ border-left: 4px solid var(--blue); background: #eff6ff; padding: 14px 16px; margin-top: 16px; }}
    img {{ max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: white; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; text-align: left; padding: 10px; font-size: 14px; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }}
    a {{ color: var(--blue); font-weight: 700; text-decoration: none; }}
    code {{ background: #eef2f7; border-radius: 4px; padding: 2px 5px; }}
    .links {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 14px; }}
    .links a {{ border: 1px solid var(--line); border-radius: 6px; padding: 9px 12px; background: #fbfdff; }}
    @media (max-width: 760px) {{
      .metric-grid, .two-col {{ grid-template-columns: 1fr; }}
      header h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Multi-Source Marketing Data Platform</h1>
    <p>Generated index for ingestion, warehouse modeling, dbt transformations, BI outputs, monitoring, semantic assets, and validation results.</p>
  </header>
  <main>
    <section>
      <h2>System Scope</h2>
      <p>This local-first platform ingests paid media, website analytics, CRM, sales, target, and mapping data; validates source quality; loads PostgreSQL; builds dbt warehouse models; and exports BI-ready reporting assets.</p>
      <div class="callout">This page links the generated outputs from the local pipeline.</div>
      <div class="links">
        <a href="reports/executive_marketing_report.html">Executive Report</a>
        <a href="reports/executive_planning_report.html">Planning Report</a>
        <a href="reports/governance_release_packet.html">Governance Packet</a>
        <a href="monitoring/observability_dashboard.html">Observability</a>
        {f'<a href="{html.escape(copied_screenshots["Executive Overview Screenshot"])}">Streamlit Dashboard Screenshots</a>' if "Executive Overview Screenshot" in copied_screenshots else ''}
      </div>
    </section>

    <section>
      <h2>Validation Status</h2>
      <div class="metric-grid">
        <div class="metric"><span>Quality Gate</span><strong>{html.escape(quality_status)}</strong></div>
        <div class="metric"><span>Checks Passed</span><strong>{passed_checks}/{len(checks)}</strong></div>
        <div class="metric"><span>Semantic Tables</span><strong>{table_count}</strong></div>
        <div class="metric"><span>Semantic Measures</span><strong>{measure_count}</strong></div>
      </div>
    </section>

    <section>
      <h2>Architecture and Dashboards</h2>
      <div class="visual-grid">
        <img src="assets/architecture_snapshot.svg" alt="Architecture snapshot">
        <img src="assets/dashboard_executive_preview.svg" alt="Executive dashboard preview">
        <img src="assets/dashboard_governance_preview.svg" alt="Governance dashboard preview">
        <img src="assets/dashboard_observability_preview.svg" alt="Observability dashboard preview">
      </div>
    </section>

    <section>
      <h2>Streamlit Dashboard Screenshots</h2>
      <p>Captured from the local dashboard using marts generated by the project pipeline.</p>
      <div class="visual-grid">{featured_screenshots}</div>
      <table>
        <thead><tr><th>Dashboard View</th><th>Image</th></tr></thead>
        <tbody>{screenshot_rows}</tbody>
      </table>
    </section>

    <section>
      <h2>Technical Documentation</h2>
      <table>
        <thead><tr><th>Document</th><th>Link</th></tr></thead>
        <tbody>{doc_rows}</tbody>
      </table>
    </section>

    <section>
      <h2>Operational Status</h2>
      <div class="two-col">
        <div>
          <h3>Generated Results</h3>
          <p>Governance status: <strong>{html.escape(str(governance_status))}</strong>.</p>
          <p>{monitoring_link}</p>
          <p>{dbt_link}</p>
        </div>
        <div>
          <h3>Signals Covered</h3>
          <ul>
            <li>source freshness</li>
            <li>rejected records</li>
            <li>schema and contract checks</li>
            <li>semantic model counts</li>
            <li>generated report availability</li>
            <li>warehouse and BI outputs</li>
          </ul>
        </div>
      </div>
    </section>

    <section>
      <h2>Artifact Manifest</h2>
      <table>
        <thead><tr><th>Artifact</th><th>Path</th><th>Status</th></tr></thead>
        <tbody>{artifact_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"""


def main() -> None:
    print(json.dumps(build_release_site(), indent=2))


if __name__ == "__main__":
    main()
