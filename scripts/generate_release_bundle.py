from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "release" / "generated"


ARTIFACTS = [
    ("Demo mart manifest", "data/exports/demo_mart_manifest.json"),
    ("Excel-ready analysis package", "reports/generated/excel_ready/README.md"),
    ("Business requirements", "docs/business_requirements.md"),
    ("Dashboard requirements", "docs/dashboard_requirements.md"),
    ("UAT checklist", "docs/uat_checklist.md"),
    ("Power BI evidence", "semantic_layer/powerbi/POWERBI_EVIDENCE.md"),
    ("Executive marketing report", "reports/generated/executive_marketing_report.html"),
    ("Executive planning report", "reports/generated/executive_planning_report.html"),
    ("Governance release packet", "reports/generated/governance_release_packet.html"),
    ("Observability dashboard", "monitoring/generated/observability_dashboard.html"),
    ("Architecture snapshot", "evidence/generated/architecture_snapshot.svg"),
    ("Dashboard wireframe", "evidence/generated/dashboard_wireframe.svg"),
    ("Executive dashboard preview", "evidence/generated/dashboard_executive_preview.svg"),
    ("Governance dashboard preview", "evidence/generated/dashboard_governance_preview.svg"),
    ("Observability dashboard preview", "evidence/generated/dashboard_observability_preview.svg"),
    ("Power BI semantic manifest", "semantic_layer/powerbi_tmdl/semantic_model_manifest.json"),
    ("Governance manifest", "governance/generated/governance_manifest.json"),
    ("Local quality gate", "local_ci/latest_quality_gate.json"),
    ("OpenLineage events", "metadata/generated/openlineage_events.jsonl"),
    ("DataHub metadata", "metadata/generated/datahub_mces.json"),
    ("Data catalog", "catalog/generated/data_catalog.json"),
    ("BI field dictionary", "catalog/generated/bi_field_dictionary.csv"),
]


def _artifact_status(relative_path: str) -> dict:
    path = PROJECT_ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        if path.exists()
        else None,
    }


def generate_release_bundle() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = [
        {"name": name, **_artifact_status(relative_path)}
        for name, relative_path in ARTIFACTS
    ]
    available = sum(1 for artifact in artifacts if artifact["exists"])
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release_name": "marketing-etl-platform-local-release",
        "status": "complete" if available == len(artifacts) else "incomplete",
        "artifact_count": len(artifacts),
        "available_artifact_count": available,
        "artifact_pass_rate": available / len(artifacts),
        "artifacts": artifacts,
        "recommended_review_order": [
            "README.md",
            "docs/business_requirements.md",
            "docs/dashboard_requirements.md",
            "evidence/generated/architecture_snapshot.svg",
            "reports/generated/executive_marketing_report.html",
            "reports/generated/excel_ready/README.md",
            "bi_app/streamlit_app.py",
            "reports/generated/executive_planning_report.html",
            "reports/generated/governance_release_packet.html",
            "semantic_layer/powerbi_tmdl/README.md",
            "docs/demo.md",
            "release/site/index.html",
        ],
    }
    (OUTPUT_DIR / "release_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "release_summary.md").write_text(_render_markdown(manifest), encoding="utf-8")
    (OUTPUT_DIR / "release_index.html").write_text(_render_html(manifest), encoding="utf-8")
    return manifest


def _render_markdown(manifest: dict) -> str:
    rows = [
        f"| {artifact['name']} | `{artifact['path']}` | {'yes' if artifact['exists'] else 'no'} | {artifact['size_bytes']:,} |"
        for artifact in manifest["artifacts"]
    ]
    order = "\n".join(f"{index + 1}. `{item}`" for index, item in enumerate(manifest["recommended_review_order"]))
    return f"""# Local Release Bundle

Generated: `{manifest['generated_at']}`

Status: `{manifest['status']}`

Artifact pass rate: `{manifest['artifact_pass_rate']:.0%}`

| Artifact | Path | Exists | Size |
|---|---|---:|---:|
{chr(10).join(rows)}

## Recommended Review Order

{order}
"""


def _render_html(manifest: dict) -> str:
    rows = []
    for artifact in manifest["artifacts"]:
        status = "available" if artifact["exists"] else "missing"
        rows.append(
            "<tr>"
            f"<td>{artifact['name']}</td>"
            f"<td><code>{artifact['path']}</code></td>"
            f"<td>{status}</td>"
            f"<td>{artifact['size_bytes']:,}</td>"
            "</tr>"
        )
    review_order = "".join(f"<li><code>{item}</code></li>" for item in manifest["recommended_review_order"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Marketing ETL Platform Release Bundle</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; margin: 40px; line-height: 1.5; }}
    h1 {{ font-size: 34px; margin-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 18px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 13px; }}
    th {{ background: #f1f5f9; }}
    .status {{ background: #f8fafc; border: 1px solid #d7dee8; border-radius: 8px; padding: 14px; margin: 18px 0; }}
  </style>
</head>
<body>
  <h1>Marketing ETL Platform Release Bundle</h1>
  <p>Generated {manifest['generated_at']}.</p>
  <div class="status">Status: <strong>{manifest['status']}</strong>. Artifact pass rate: <strong>{manifest['artifact_pass_rate']:.0%}</strong>.</div>
  <table><thead><tr><th>Artifact</th><th>Path</th><th>Status</th><th>Size</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  <h2>Recommended Review Order</h2>
  <ol>{review_order}</ol>
</body>
</html>"""


def main() -> None:
    print(json.dumps(generate_release_bundle(), indent=2))


if __name__ == "__main__":
    main()
