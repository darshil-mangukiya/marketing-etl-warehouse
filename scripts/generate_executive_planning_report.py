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

from scripts.build_demo_marts import build_demo_marts

REPORT_DIR = PROJECT_ROOT / "reports" / "generated"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"


def _read_demo_table(name: str) -> pd.DataFrame:
    path = EXPORT_DIR / f"demo_{name}.csv"
    if not path.exists():
        build_demo_marts()
    return pd.read_csv(path)


def generate_executive_planning_report() -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    build_demo_marts()
    scorecard = _read_demo_table("mart_executive_scorecard")
    briefing = _read_demo_table("mart_executive_briefing")
    actions = _read_demo_table("mart_action_center")
    forecast = _read_demo_table("mart_performance_forecast")
    scenarios = _read_demo_table("mart_budget_scenarios")
    data_product = _read_demo_table("mart_data_product_scorecard")
    kpis = _read_demo_table("mart_semantic_kpi_governance")
    source_health = _read_demo_table("mart_source_health")

    metrics = _planning_metrics(scorecard, actions, forecast, scenarios, data_product)
    html_path = REPORT_DIR / "executive_planning_report.html"
    markdown_path = REPORT_DIR / "executive_planning_report.md"
    html_path.write_text(
        _render_html(metrics, scorecard, briefing, actions, forecast, scenarios, data_product, kpis, source_health),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(metrics, briefing, actions, data_product), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "html": str(html_path.relative_to(PROJECT_ROOT)),
        "markdown": str(markdown_path.relative_to(PROJECT_ROOT)),
        "metrics": metrics,
        "included_marts": [
            "mart_executive_scorecard",
            "mart_executive_briefing",
            "mart_action_center",
            "mart_performance_forecast",
            "mart_budget_scenarios",
            "mart_data_product_scorecard",
            "mart_semantic_kpi_governance",
            "mart_source_health",
        ],
    }
    (REPORT_DIR / "executive_planning_report_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _planning_metrics(
    scorecard: pd.DataFrame,
    actions: pd.DataFrame,
    forecast: pd.DataFrame,
    scenarios: pd.DataFrame,
    data_product: pd.DataFrame,
) -> dict:
    if forecast.empty:
        forecast_spend = forecast_revenue = forecast_margin = 0.0
    else:
        forecast_spend = float(pd.to_numeric(forecast.get("forecast_spend", 0), errors="coerce").fillna(0).sum())
        forecast_revenue = float(pd.to_numeric(forecast.get("forecast_booked_revenue", 0), errors="coerce").fillna(0).sum())
        forecast_margin = float(pd.to_numeric(forecast.get("forecast_gross_margin", 0), errors="coerce").fillna(0).sum())

    if scenarios.empty:
        approved_scenarios = 0
        best_incremental_margin = 0.0
    else:
        approved = scenarios[scenarios["decision"].eq("approve")] if "decision" in scenarios.columns else pd.DataFrame()
        approved_scenarios = len(approved)
        best_incremental_margin = (
            float(pd.to_numeric(approved.get("incremental_margin", 0), errors="coerce").fillna(0).max())
            if not approved.empty
            else 0.0
        )

    if actions.empty:
        p0_actions = p1_actions = urgent_actions = 0
        action_value = 0.0
    else:
        p0_actions = int(actions.get("priority", pd.Series(dtype=str)).eq("P0").sum())
        p1_actions = int(actions.get("priority", pd.Series(dtype=str)).eq("P1").sum())
        due = pd.to_numeric(actions.get("due_in_days", 0), errors="coerce").fillna(0)
        urgent_actions = int((actions.get("priority", pd.Series(dtype=str)).isin(["P0", "P1"]) & (due <= 2)).sum())
        action_value = float(pd.to_numeric(actions.get("action_value", 0), errors="coerce").fillna(0).sum())

    avg_data_product_score = 0.0 if data_product.empty else float(pd.to_numeric(data_product["score"], errors="coerce").mean())
    at_risk_domains = 0 if data_product.empty else int(data_product["score_status"].eq("at_risk").sum())
    executive_status = "unknown" if scorecard.empty else str(scorecard.iloc[0].get("executive_status", "unknown"))

    return {
        "executive_status": executive_status,
        "forecast_spend": forecast_spend,
        "forecast_revenue": forecast_revenue,
        "forecast_margin": forecast_margin,
        "forecast_roas": forecast_revenue / forecast_spend if forecast_spend else 0,
        "approved_scenarios": approved_scenarios,
        "best_incremental_margin": best_incremental_margin,
        "p0_actions": p0_actions,
        "p1_actions": p1_actions,
        "urgent_actions": urgent_actions,
        "action_value": action_value,
        "avg_data_product_score": avg_data_product_score,
        "at_risk_domains": at_risk_domains,
    }


def _render_html(
    metrics: dict,
    scorecard: pd.DataFrame,
    briefing: pd.DataFrame,
    actions: pd.DataFrame,
    forecast: pd.DataFrame,
    scenarios: pd.DataFrame,
    data_product: pd.DataFrame,
    kpis: pd.DataFrame,
    source_health: pd.DataFrame,
) -> str:
    score = {} if scorecard.empty else scorecard.iloc[0].to_dict()
    briefing_rows = _table_rows(briefing.head(10), ["priority", "section", "finding", "recommended_action", "evidence_metric"])
    action_rows = _table_rows(
        actions.head(15),
        ["priority", "owner_team", "action_type", "title", "business_impact", "due_in_days"],
    )
    scenario_rows = _table_rows(
        scenarios.sort_values("incremental_margin", ascending=False).head(15) if not scenarios.empty else scenarios,
        ["scenario_name", "normalized_channel", "projected_spend", "projected_revenue", "projected_roas", "incremental_margin", "decision"],
    )
    forecast_rows = _table_rows(
        forecast.head(18),
        ["forecast_month", "normalized_channel", "forecast_spend", "forecast_booked_revenue", "forecast_roas", "forecast_confidence"],
    )
    data_product_rows = _table_rows(
        data_product,
        ["scorecard_domain", "owner_team", "score", "score_status", "risk_count", "next_action"],
    )
    kpi_rows = _table_rows(kpis, ["kpi_name", "owner_team", "certified_status", "target_or_guardrail", "dashboard_pages"])
    source_rows = _table_rows(source_health, ["source_system", "rows", "accepted", "rejected", "source_health_status"])
    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Executive Planning and Governance Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; margin: 40px; line-height: 1.5; }}
    h1 {{ font-size: 34px; margin-bottom: 4px; }}
    h2 {{ margin-top: 34px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0; }}
    .card {{ border: 1px solid #d7dee8; border-radius: 8px; padding: 15px; background: #f8fafc; }}
    .label {{ color: #64748b; font-size: 13px; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 13px; vertical-align: top; }}
    th {{ background: #f1f5f9; }}
    .note {{ background: #eef6ff; border-left: 5px solid #2563eb; padding: 14px 18px; margin: 18px 0; }}
    @media print {{ body {{ margin: 22mm; }} h2 {{ break-after: avoid; }} table {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
  <h1>Executive Planning and Governance Report</h1>
  <p>Generated {html.escape(generated_at)}. This artifact packages planning, action ownership, KPI governance, and data-product health for leadership review.</p>
  <div class="grid">
    {_card("Executive Status", str(metrics["executive_status"]).replace("_", " ").title())}
    {_card("3-Month Forecast ROAS", f"{metrics['forecast_roas']:.2f}x")}
    {_card("Approved Scenarios", f"{metrics['approved_scenarios']:,}")}
    {_card("Avg Data Product Score", f"{metrics['avg_data_product_score']:.1f}")}
    {_card("Forecast Spend", _money(metrics["forecast_spend"]))}
    {_card("Forecast Revenue", _money(metrics["forecast_revenue"]))}
    {_card("Forecast Margin", _money(metrics["forecast_margin"]))}
    {_card("Best Incremental Margin", _money(metrics["best_incremental_margin"]))}
    {_card("P0 Actions", f"{metrics['p0_actions']:,}")}
    {_card("P1 Actions", f"{metrics['p1_actions']:,}")}
    {_card("Urgent Actions", f"{metrics['urgent_actions']:,}")}
    {_card("Action Value", _money(metrics["action_value"]))}
  </div>

  <div class="note">Board narrative: {html.escape(str(score.get("board_narrative", "No board narrative generated.")))}</div>

  <h2>Decision Briefing</h2>
  <table><thead><tr><th>Priority</th><th>Section</th><th>Finding</th><th>Recommended Action</th><th>Supporting Metric</th></tr></thead><tbody>{briefing_rows}</tbody></table>

  <h2>Open Action Queue</h2>
  <table><thead><tr><th>Priority</th><th>Owner</th><th>Type</th><th>Title</th><th>Business Impact</th><th>Due Days</th></tr></thead><tbody>{action_rows}</tbody></table>

  <h2>Forecast and Budget Scenarios</h2>
  <table><thead><tr><th>Month</th><th>Channel</th><th>Spend</th><th>Revenue</th><th>ROAS</th><th>Confidence</th></tr></thead><tbody>{forecast_rows}</tbody></table>
  <table><thead><tr><th>Scenario</th><th>Channel</th><th>Projected Spend</th><th>Projected Revenue</th><th>Projected ROAS</th><th>Incremental Margin</th><th>Decision</th></tr></thead><tbody>{scenario_rows}</tbody></table>

  <h2>Data Product Operating Scorecard</h2>
  <table><thead><tr><th>Domain</th><th>Owner</th><th>Score</th><th>Status</th><th>Risks</th><th>Next Action</th></tr></thead><tbody>{data_product_rows}</tbody></table>

  <h2>Certified KPI Governance</h2>
  <table><thead><tr><th>KPI</th><th>Owner</th><th>Status</th><th>Guardrail</th><th>Dashboard Pages</th></tr></thead><tbody>{kpi_rows}</tbody></table>

  <h2>Source Health</h2>
  <table><thead><tr><th>Source</th><th>Rows</th><th>Accepted</th><th>Rejected</th><th>Status</th></tr></thead><tbody>{source_rows}</tbody></table>
</body>
</html>"""


def _render_markdown(
    metrics: dict,
    briefing: pd.DataFrame,
    actions: pd.DataFrame,
    data_product: pd.DataFrame,
) -> str:
    top_findings = []
    for _, row in briefing.head(5).iterrows():
        top_findings.append(f"- `{row.get('priority', 'P?')}` {row.get('section', 'Unknown')}: {row.get('finding', '')}")
    urgent = actions[actions.get("priority", pd.Series(dtype=str)).isin(["P0", "P1"])].head(8) if not actions.empty else pd.DataFrame()
    urgent_lines = []
    for _, row in urgent.iterrows():
        urgent_lines.append(f"- `{row.get('priority')}` {row.get('owner_team')}: {row.get('title')}")
    governance_lines = []
    governance_source = data_product.sort_values("score").head(5) if not data_product.empty else pd.DataFrame()
    for _, row in governance_source.iterrows():
        governance_lines.append(f"- `{row.get('score_status')}` {row.get('scorecard_domain')}: score {row.get('score')}")
    return f"""# Executive Planning and Governance Report

Generated: `{datetime.now(timezone.utc).isoformat()}`

| Metric | Value |
|---|---:|
| Executive Status | {str(metrics['executive_status']).replace('_', ' ').title()} |
| Forecast ROAS | {metrics['forecast_roas']:.2f}x |
| Forecast Revenue | {_money(metrics['forecast_revenue'])} |
| Forecast Margin | {_money(metrics['forecast_margin'])} |
| Approved Scenarios | {metrics['approved_scenarios']:,} |
| Best Incremental Margin | {_money(metrics['best_incremental_margin'])} |
| P0 Actions | {metrics['p0_actions']:,} |
| P1 Actions | {metrics['p1_actions']:,} |
| Avg Data Product Score | {metrics['avg_data_product_score']:.1f} |

## Top Findings

{chr(10).join(top_findings) if top_findings else "- No findings generated."}

## Urgent Action Queue

{chr(10).join(urgent_lines) if urgent_lines else "- No urgent P0/P1 actions generated."}

## Lowest Governance Scores

{chr(10).join(governance_lines) if governance_lines else "- No governance scorecard rows generated."}
"""


def _card(label: str, value: str) -> str:
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{html.escape(value)}</div></div>'


def _money(value: float) -> str:
    return f"${float(value):,.0f}"


def _table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return f'<tr><td colspan="{len(columns)}">No rows available.</td></tr>'
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float) and any(token in column for token in ["spend", "revenue", "margin", "value"]):
                value = _money(value)
            elif isinstance(value, float) and ("roas" in column or "rate" in column):
                value = f"{value:.2f}"
            elif isinstance(value, float):
                value = f"{value:.2f}"
            cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(rows)


def main() -> None:
    print(json.dumps(generate_executive_planning_report(), indent=2))


if __name__ == "__main__":
    main()
