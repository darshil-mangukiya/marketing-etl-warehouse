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


def _read_demo_table(name: str) -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "exports" / f"demo_{name}.csv"
    if not path.exists():
        build_demo_marts()
    return pd.read_csv(path)


def generate_executive_report() -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    build_demo_marts()
    channel = _read_demo_table("mart_channel_performance")
    campaign = _read_demo_table("mart_campaign_performance")
    target = _read_demo_table("mart_target_vs_actual")
    attribution = _read_demo_table("mart_attribution_summary")
    comparison = _read_demo_table("mart_attribution_model_comparison")
    quality = _read_demo_table("mart_data_quality_monitoring")
    scorecard_path = PROJECT_ROOT / "ops" / "generated" / "operational_scorecard.json"
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8")) if scorecard_path.exists() else {}

    metrics = _executive_metrics(channel, quality)
    html_path = REPORT_DIR / "executive_marketing_report.html"
    md_path = REPORT_DIR / "executive_marketing_report.md"
    html_path.write_text(
        _render_html(metrics, channel, campaign, target, attribution, comparison, quality, scorecard),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(metrics, campaign, scorecard), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "html": str(html_path.relative_to(PROJECT_ROOT)),
        "markdown": str(md_path.relative_to(PROJECT_ROOT)),
        "metrics": metrics,
        "pdf_note": "Open the HTML report in a browser and print to PDF for a polished PDF artifact.",
    }
    (REPORT_DIR / "executive_report_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _executive_metrics(channel: pd.DataFrame, quality: pd.DataFrame) -> dict:
    spend = float(channel.get("spend", pd.Series(dtype=float)).sum())
    revenue = float(channel.get("booked_revenue", pd.Series(dtype=float)).sum())
    margin = float(channel.get("gross_margin", pd.Series(dtype=float)).sum())
    conversions = float(channel.get("closed_won_conversions", pd.Series(dtype=float)).sum())
    rejected = int(quality.get("rejected_count", pd.Series(dtype=float)).sum()) if not quality.empty else 0
    return {
        "spend": spend,
        "booked_revenue": revenue,
        "gross_margin": margin,
        "roas": revenue / spend if spend else 0,
        "cac": spend / conversions if conversions else 0,
        "rejected_rows": rejected,
    }


def _render_html(
    metrics: dict,
    channel: pd.DataFrame,
    campaign: pd.DataFrame,
    target: pd.DataFrame,
    attribution: pd.DataFrame,
    comparison: pd.DataFrame,
    quality: pd.DataFrame,
    scorecard: dict,
) -> str:
    top_campaigns = campaign.sort_values("spend", ascending=False).head(10) if not campaign.empty else pd.DataFrame()
    budget = channel.sort_values("spend", ascending=False).head(10) if not channel.empty else pd.DataFrame()
    attribution_rows = _table_rows(attribution.head(18), ["reporting_month", "attribution_model", "attributed_revenue", "weighted_conversions"])
    comparison_rows = _table_rows(comparison.head(12), ["reporting_month", "first_touch_revenue", "last_touch_revenue", "linear_revenue", "time_decay_revenue"])
    campaign_rows = _table_rows(top_campaigns, ["campaign_name", "normalized_channel", "spend", "attributed_roas", "waste_budget_flag"])
    target_rows = _table_rows(target.head(12), ["target_month", "region", "channel", "spend_attainment", "revenue_attainment", "lead_attainment"])
    quality_rows = _table_rows(quality.head(12), ["source_system", "status", "rejected_count", "monitoring_status"])
    budget_rows = _table_rows(budget, ["reporting_month", "channel_name", "spend", "roas", "cac"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Executive Marketing Performance Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; margin: 40px; line-height: 1.5; }}
    h1 {{ font-size: 34px; margin-bottom: 4px; }}
    h2 {{ margin-top: 34px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 24px 0; }}
    .card {{ border: 1px solid #d7dee8; border-radius: 8px; padding: 15px; background: #f8fafc; }}
    .label {{ color: #64748b; font-size: 13px; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 13px; }}
    th {{ background: #f1f5f9; }}
    .note {{ background: #fff7ed; border-left: 5px solid #f97316; padding: 14px 18px; margin: 18px 0; }}
    @media print {{ body {{ margin: 22mm; }} .pagebreak {{ page-break-before: always; }} }}
  </style>
</head>
<body>
  <h1>Executive Marketing Performance Report</h1>
  <p>Generated {html.escape(datetime.now(timezone.utc).isoformat())}. Data reflects the current local mart/demo export layer.</p>
  <div class="grid">
    {_card("Spend", _money(metrics["spend"]))}
    {_card("Booked Revenue", _money(metrics["booked_revenue"]))}
    {_card("Gross Margin", _money(metrics["gross_margin"]))}
    {_card("ROAS", f"{metrics['roas']:.2f}x")}
    {_card("CAC", _money(metrics["cac"]))}
  </div>
  <div class="note">Operational status: {html.escape(str(scorecard.get('overall_status', 'unknown')))}. Rejected rows captured by quality checks: {metrics['rejected_rows']:,}.</div>

  <h2>Executive Readout</h2>
  <p>Marketing performance is summarized across spend efficiency, revenue contribution, attribution sensitivity, target attainment, and source health. The report intentionally includes data quality context so leaders can separate business signals from source reliability issues.</p>

  <h2>Budget Efficiency</h2>
  <table><thead><tr><th>Month</th><th>Channel</th><th>Spend</th><th>ROAS</th><th>CAC</th></tr></thead><tbody>{budget_rows}</tbody></table>

  <h2>Campaign Intelligence</h2>
  <table><thead><tr><th>Campaign</th><th>Channel</th><th>Spend</th><th>Attributed ROAS</th><th>Waste Flag</th></tr></thead><tbody>{campaign_rows}</tbody></table>

  <h2>Advanced Attribution</h2>
  <table><thead><tr><th>Month</th><th>Model</th><th>Revenue</th><th>Weighted Conversions</th></tr></thead><tbody>{attribution_rows}</tbody></table>
  <table><thead><tr><th>Month</th><th>First Touch</th><th>Last Touch</th><th>Linear</th><th>Time Decay</th></tr></thead><tbody>{comparison_rows}</tbody></table>

  <h2>Target Attainment</h2>
  <table><thead><tr><th>Month</th><th>Region</th><th>Channel</th><th>Spend Attainment</th><th>Revenue Attainment</th><th>Lead Attainment</th></tr></thead><tbody>{target_rows}</tbody></table>

  <h2>Data Quality Notes</h2>
  <table><thead><tr><th>Source</th><th>Status</th><th>Rejected</th><th>Monitoring Status</th></tr></thead><tbody>{quality_rows}</tbody></table>
</body>
</html>"""


def _render_markdown(metrics: dict, campaign: pd.DataFrame, scorecard: dict) -> str:
    top_campaign = campaign.sort_values("spend", ascending=False).head(1) if not campaign.empty else pd.DataFrame()
    campaign_name = top_campaign.iloc[0].get("campaign_name") if not top_campaign.empty else "n/a"
    return f"""# Executive Marketing Performance Report

Generated: `{datetime.now(timezone.utc).isoformat()}`

| KPI | Value |
|---|---:|
| Spend | {_money(metrics['spend'])} |
| Booked Revenue | {_money(metrics['booked_revenue'])} |
| Gross Margin | {_money(metrics['gross_margin'])} |
| ROAS | {metrics['roas']:.2f}x |
| CAC | {_money(metrics['cac'])} |
| Rejected Rows | {metrics['rejected_rows']:,} |

Top spend campaign: `{campaign_name}`

Operational status: `{scorecard.get('overall_status', 'unknown')}`
"""


def _card(label: str, value: str) -> str:
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{html.escape(value)}</div></div>'


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return f'<tr><td colspan="{len(columns)}">No rows available.</td></tr>'
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float) and ("revenue" in column or "spend" in column or column in {"cac"}):
                value = _money(value)
            elif isinstance(value, float):
                value = f"{value:.2f}"
            cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(rows)


def main() -> None:
    print(json.dumps(generate_executive_report(), indent=2))


if __name__ == "__main__":
    main()
