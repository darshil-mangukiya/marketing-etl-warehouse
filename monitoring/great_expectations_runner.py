from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from monitoring.quality_checks import run_quality_checks


def run_checkpoint(profile: str = "dev") -> dict:
    """Run a GE-compatible checkpoint and generate local Data Docs-style evidence.

    The project ships native Great Expectations config and expectation suites. This
    runner remains lightweight for local validation: when the optional
    GE package is unavailable, it uses the project's custom validator and writes
    checkpoint artifacts with the same operational shape.
    """

    config = PlatformConfig.from_env()
    config.ensure_dirs()
    ge_available = _great_expectations_available()
    summary = run_quality_checks(profile=profile)
    checkpoint = {
        "checkpoint_name": "marketing_raw_checkpoint",
        "profile": profile,
        "ge_available": ge_available,
        "run_time": datetime.now(timezone.utc).isoformat(),
        "success": summary["rejected_count"] == 0,
        "quality_gate": "pass" if _rejected_rate(summary) < 0.05 else "quarantine",
        "statistics": {
            "evaluated_files": summary["file_count"],
            "evaluated_rows": summary["row_count"],
            "rejected_rows": summary["rejected_count"],
        },
        "validation_reports": summary["reports"],
    }
    output_dir = config.quality_report_dir / "great_expectations"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "marketing_raw_checkpoint_result.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, default=str), encoding="utf-8")
    docs_path = output_dir / "data_docs" / "index.html"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_text(_render_data_docs(checkpoint), encoding="utf-8")
    return {
        **checkpoint,
        "checkpoint_result": str(checkpoint_path.relative_to(config.project_root)),
        "data_docs": str(docs_path.relative_to(config.project_root)),
    }


def _great_expectations_available() -> bool:
    try:
        import great_expectations  # noqa: F401

        return True
    except Exception:
        return False


def _rejected_rate(summary: dict) -> float:
    return summary["rejected_count"] / summary["row_count"] if summary["row_count"] else 0.0


def _render_data_docs(checkpoint: dict) -> str:
    rows = []
    for report in checkpoint["validation_reports"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(report['source_system'])}</td>"
            f"<td>{html.escape(report['file'])}</td>"
            f"<td>{report['row_count']}</td>"
            f"<td>{report['rejected_count']}</td>"
            f"<td>{html.escape(report['status'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Marketing Raw Checkpoint</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
    .hero {{ border-left: 6px solid #1677ff; padding-left: 18px; margin-bottom: 24px; }}
    .metric {{ display: inline-block; margin-right: 24px; padding: 12px 16px; border: 1px solid #d8dee9; border-radius: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 24px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; font-size: 14px; }}
    th {{ background: #f8fafc; }}
  </style>
</head>
<body>
  <section class="hero">
    <h1>Marketing Raw Checkpoint</h1>
    <p>Generated {html.escape(checkpoint['run_time'])}. GE package available: {checkpoint['ge_available']}.</p>
  </section>
  <div class="metric"><strong>Files</strong><br>{checkpoint['statistics']['evaluated_files']}</div>
  <div class="metric"><strong>Rows</strong><br>{checkpoint['statistics']['evaluated_rows']}</div>
  <div class="metric"><strong>Rejected Rows</strong><br>{checkpoint['statistics']['rejected_rows']}</div>
  <div class="metric"><strong>Quality Gate</strong><br>{html.escape(checkpoint['quality_gate'])}</div>
  <table>
    <thead><tr><th>Source</th><th>File</th><th>Rows</th><th>Rejected</th><th>Status</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Great Expectations-compatible raw data checkpoint.")
    parser.add_argument("--profile", default="dev")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_checkpoint(profile=args.profile), indent=2, default=str))


if __name__ == "__main__":
    main()
