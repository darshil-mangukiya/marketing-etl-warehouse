from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ops.scorecard import build_scorecard


def _load_json(path: Path, default: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def generate_observability_report() -> dict:
    scorecard = build_scorecard()
    quality = _load_json(PROJECT_ROOT / "data" / "quality_reports" / "latest_quality_summary.json", {})
    contracts = _load_csv(PROJECT_ROOT / "data" / "quality_reports" / "contracts" / "contract_check_results.csv")
    source_health = _load_csv(PROJECT_ROOT / "data" / "quality_reports" / "source_health_summary.csv")
    benchmark = _load_json(PROJECT_ROOT / "benchmarks" / "results" / "pipeline_benchmark_latest.json", {})
    local_gate = _load_json(PROJECT_ROOT / "local_ci" / "latest_quality_gate.json", {})
    alerts = _load_alerts(PROJECT_ROOT / "data" / "logs" / "alerts.jsonl")

    output_dir = PROJECT_ROOT / "monitoring" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "observability_dashboard.html"
    md_path = output_dir / "observability_dashboard.md"
    html_path.write_text(
        _render_html(scorecard, quality, contracts, source_health, benchmark, local_gate, alerts),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(scorecard, quality, contracts, benchmark, local_gate), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "html": str(html_path.relative_to(PROJECT_ROOT)),
        "markdown": str(md_path.relative_to(PROJECT_ROOT)),
        "overall_status": scorecard["overall_status"],
    }
    (output_dir / "observability_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _load_alerts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _render_html(
    scorecard: dict,
    quality: dict,
    contracts: pd.DataFrame,
    source_health: pd.DataFrame,
    benchmark: dict,
    local_gate: dict,
    alerts: list[dict],
) -> str:
    contract_rows = _table_rows(
        contracts.head(20),
        ["source_system", "rule_name", "severity", "failed_count", "detail"],
    )
    source_rows = _table_rows(
        source_health.head(20),
        ["source_system", "last_ingestion_time", "failed_loads", "rejected_rows", "health_status"],
    )
    alert_rows = "".join(
        "<tr>"
        f"<td>{html.escape(alert.get('created_at', ''))}</td>"
        f"<td>{html.escape(alert.get('severity', ''))}</td>"
        f"<td>{html.escape(alert.get('alert_type', ''))}</td>"
        f"<td>{html.escape(alert.get('message', ''))}</td>"
        "</tr>"
        for alert in alerts[-20:]
    )
    checks = local_gate.get("checks", [])
    check_rows = "".join(
        "<tr>"
        f"<td>{html.escape(check.get('command', ''))}</td>"
        f"<td>{html.escape(check.get('status', ''))}</td>"
        f"<td>{check.get('return_code')}</td>"
        "</tr>"
        for check in checks
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Marketing Platform Observability</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f8fafc; }}
    h1 {{ margin-bottom: 4px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 24px 0; }}
    .card {{ background: white; border: 1px solid #d7dee8; border-radius: 8px; padding: 16px; }}
    .label {{ color: #64748b; font-size: 13px; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; margin: 12px 0 28px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 9px; text-align: left; font-size: 13px; vertical-align: top; }}
    th {{ background: #f1f5f9; }}
    .watch {{ color: #b45309; }}
    .healthy {{ color: #15803d; }}
  </style>
</head>
<body>
  <h1>Marketing Data Platform Observability</h1>
  <p>Generated {html.escape(datetime.now(timezone.utc).isoformat())}</p>
  <div class="grid">
    {_card("Overall Status", scorecard.get("overall_status", "unknown"))}
    {_card("Quality Gate", scorecard.get("quality", {}).get("quality_gate"))}
    {_card("Rejected Rows", scorecard.get("quality", {}).get("rejected_count"))}
    {_card("Contract Issues", scorecard.get("contracts", {}).get("issue_count"))}
    {_card("Catalog Models", scorecard.get("catalog", {}).get("models"))}
    {_card("Lineage Edges", scorecard.get("catalog", {}).get("lineage_edges"))}
    {_card("Benchmark", benchmark.get("status"))}
    {_card("Quality Gate Checks", len(checks))}
  </div>
  <h2>Quality Summary</h2>
  <p>Rows evaluated: {quality.get('row_count')}; rejected rows: {quality.get('rejected_count')}; status: {html.escape(str(quality.get('status')))}.</p>
  <h2>Contract Findings</h2>
  <table><thead><tr><th>Source</th><th>Rule</th><th>Severity</th><th>Failed</th><th>Detail</th></tr></thead><tbody>{contract_rows}</tbody></table>
  <h2>Source Health</h2>
  <table><thead><tr><th>Source</th><th>Last Ingestion</th><th>Failed Loads</th><th>Rejected Rows</th><th>Status</th></tr></thead><tbody>{source_rows}</tbody></table>
  <h2>Local Quality Gate</h2>
  <table><thead><tr><th>Command</th><th>Status</th><th>Return Code</th></tr></thead><tbody>{check_rows}</tbody></table>
  <h2>Recent Alerts</h2>
  <table><thead><tr><th>Created</th><th>Severity</th><th>Type</th><th>Message</th></tr></thead><tbody>{alert_rows}</tbody></table>
</body>
</html>"""


def _card(label: str, value) -> str:
    value_text = html.escape(str(value if value is not None else "n/a"))
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{value_text}</div></div>'


def _table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return f'<tr><td colspan="{len(columns)}">No rows available.</td></tr>'
    rows = []
    for _, row in frame.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>")
    return "".join(rows)


def _render_markdown(scorecard: dict, quality: dict, contracts: pd.DataFrame, benchmark: dict, local_gate: dict) -> str:
    benchmark_status = benchmark.get("status") or "n/a"
    return f"""# Marketing Platform Observability

Generated: `{datetime.now(timezone.utc).isoformat()}`

| Area | Signal |
|---|---|
| Overall status | {scorecard.get('overall_status')} |
| Quality gate | {scorecard.get('quality', {}).get('quality_gate')} |
| Rows evaluated | {quality.get('row_count')} |
| Rejected rows | {quality.get('rejected_count')} |
| Contract issues | {len(contracts[contracts['severity'].ne('info')]) if not contracts.empty and 'severity' in contracts else 0} |
| Benchmark status | {benchmark_status} |
| Local quality gate | {local_gate.get('status')} |
"""


def main() -> None:
    print(json.dumps(generate_observability_report(), indent=2))


if __name__ == "__main__":
    main()
