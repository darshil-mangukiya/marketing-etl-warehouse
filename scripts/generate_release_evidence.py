from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_demo_marts import build_demo_marts

EVIDENCE_DIR = PROJECT_ROOT / "evidence" / "generated"


def _read_csv_optional(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size <= 1:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


def generate_evidence() -> dict:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    build_demo_marts()
    channel = _read_csv_optional(PROJECT_ROOT / "data" / "exports" / "demo_mart_channel_performance.csv")
    quality = _read_csv_optional(PROJECT_ROOT / "data" / "exports" / "demo_mart_data_quality_monitoring.csv")
    campaign = _read_csv_optional(PROJECT_ROOT / "data" / "exports" / "demo_mart_campaign_performance.csv")
    action_center = _read_csv_optional(PROJECT_ROOT / "data" / "exports" / "demo_mart_action_center.csv")
    source_health = _read_csv_optional(PROJECT_ROOT / "data" / "exports" / "demo_mart_source_health.csv")

    metrics = {
        "spend": float(channel["spend"].sum()) if "spend" in channel else 0,
        "revenue": float(channel["booked_revenue"].sum()) if "booked_revenue" in channel else 0,
        "roas": float(channel["booked_revenue"].sum() / channel["spend"].sum()) if channel["spend"].sum() else 0,
        "campaigns": int(campaign["campaign_id"].nunique()) if "campaign_id" in campaign else 0,
        "quality_files": int(len(quality)),
        "rejected_rows": int(quality["rejected_count"].sum()) if "rejected_count" in quality else 0,
    }

    architecture_path = EVIDENCE_DIR / "architecture_snapshot.svg"
    architecture_path.write_text(_architecture_svg(), encoding="utf-8")

    dashboard_path = EVIDENCE_DIR / "dashboard_wireframe.svg"
    dashboard_path.write_text(_dashboard_svg(metrics), encoding="utf-8")

    executive_preview_path = EVIDENCE_DIR / "dashboard_executive_preview.svg"
    executive_preview_path.write_text(_executive_dashboard_svg(channel), encoding="utf-8")

    governance_preview_path = EVIDENCE_DIR / "dashboard_governance_preview.svg"
    governance_preview_path.write_text(_governance_dashboard_svg(action_center), encoding="utf-8")

    observability_preview_path = EVIDENCE_DIR / "dashboard_observability_preview.svg"
    observability_preview_path.write_text(_observability_dashboard_svg(source_health, quality), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": [
            str(architecture_path.relative_to(PROJECT_ROOT)),
            str(dashboard_path.relative_to(PROJECT_ROOT)),
            str(executive_preview_path.relative_to(PROJECT_ROOT)),
            str(governance_preview_path.relative_to(PROJECT_ROOT)),
            str(observability_preview_path.relative_to(PROJECT_ROOT)),
        ],
        "metrics": metrics,
    }
    manifest_path = EVIDENCE_DIR / "evidence_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _architecture_svg() -> str:
    boxes = [
        ("Source APIs", 40, 80, "#e6f4ff"),
        ("Python Ingestion", 260, 80, "#f0fdf4"),
        ("S3-Style Lake", 480, 80, "#fff7ed"),
        ("PostgreSQL", 700, 80, "#f8fafc"),
        ("dbt Warehouse", 920, 80, "#eef2ff"),
        ("BI + Semantic", 1140, 80, "#fdf2f8"),
        ("Quality + Monitoring", 480, 245, "#fef2f2"),
        ("Airflow Orchestration", 700, 245, "#ecfeff"),
    ]
    rects = []
    for label, x, y, color in boxes:
        rects.append(
            f'<rect x="{x}" y="{y}" width="170" height="78" rx="8" fill="{color}" stroke="#334155"/>'
            f'<text x="{x + 85}" y="{y + 45}" text-anchor="middle" font-size="16" fill="#0f172a">{label}</text>'
        )
    arrows = []
    for x1, y1, x2, y2 in [
        (210, 119, 260, 119),
        (430, 119, 480, 119),
        (650, 119, 700, 119),
        (870, 119, 920, 119),
        (1090, 119, 1140, 119),
        (565, 158, 565, 245),
        (785, 158, 785, 245),
    ]:
        arrows.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#0f172a" stroke-width="2" marker-end="url(#arrow)"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1360" height="390" viewBox="0 0 1360 390">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#0f172a"/>
    </marker>
  </defs>
  <rect width="1360" height="390" fill="#ffffff"/>
  <text x="40" y="42" font-size="26" font-weight="700" fill="#0f172a">Campaign ROI Reporting Platform</text>
  {''.join(rects)}
  {''.join(arrows)}
  <text x="480" y="355" font-size="14" fill="#475569">APIs, ingestion, lake, warehouse, marts, semantic layer, orchestration, and monitoring.</text>
</svg>"""


def _dashboard_svg(metrics: dict) -> str:
    spend = _money(metrics["spend"])
    revenue = _money(metrics["revenue"])
    roas = f"{metrics['roas']:.2f}x"
    campaigns = f"{metrics['campaigns']:,}"
    cards = [
        ("Spend", spend, 45),
        ("Booked Revenue", revenue, 295),
        ("ROAS", roas, 545),
        ("Campaigns", campaigns, 795),
        ("Rejected Rows", f"{metrics['rejected_rows']:,}", 1045),
    ]
    card_svg = []
    for label, value, x in cards:
        card_svg.append(
            f'<rect x="{x}" y="88" width="210" height="96" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>'
            f'<text x="{x + 18}" y="123" font-size="15" fill="#64748b">{html.escape(label)}</text>'
            f'<text x="{x + 18}" y="160" font-size="26" font-weight="700" fill="#0f172a">{html.escape(value)}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="760" viewBox="0 0 1300 760">
  <rect width="1300" height="760" fill="#ffffff"/>
  <text x="45" y="52" font-size="28" font-weight="700" fill="#0f172a">Executive Marketing Overview</text>
  {''.join(card_svg)}
  <rect x="45" y="230" width="590" height="230" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="70" y="268" font-size="18" font-weight="700" fill="#0f172a">Spend and Revenue Trend</text>
  <polyline points="85,410 170,376 255,390 340,330 425,352 510,300 600,288" fill="none" stroke="#2563eb" stroke-width="4"/>
  <polyline points="85,430 170,418 255,404 340,384 425,360 510,340 600,320" fill="none" stroke="#16a34a" stroke-width="4"/>
  <rect x="670" y="230" width="585" height="230" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="695" y="268" font-size="18" font-weight="700" fill="#0f172a">Channel Efficiency Map</text>
  <circle cx="760" cy="380" r="34" fill="#bfdbfe" stroke="#2563eb"/>
  <circle cx="905" cy="315" r="48" fill="#bbf7d0" stroke="#16a34a"/>
  <circle cx="1085" cy="395" r="26" fill="#fecaca" stroke="#dc2626"/>
  <rect x="45" y="500" width="1210" height="190" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="70" y="540" font-size="18" font-weight="700" fill="#0f172a">Quality and Pipeline Health</text>
  <text x="70" y="590" font-size="16" fill="#334155">GE checkpoint, rejected-row outputs, source health, and freshness checks feed the monitoring page.</text>
  <text x="70" y="630" font-size="16" fill="#334155">Dashboard artifact generated from local smoke marts for release review.</text>
</svg>"""


def _executive_dashboard_svg(channel: pd.DataFrame) -> str:
    ordered = channel.sort_values("spend", ascending=False).head(6).copy()
    max_spend = float(ordered["spend"].max()) if not ordered.empty else 1.0
    rows = []
    for index, row in enumerate(ordered.itertuples(index=False), start=0):
        y = 175 + index * 54
        width = max(28, int(float(row.spend) / max_spend * 360))
        rows.append(
            f'<text x="72" y="{y + 20}" font-size="15" fill="#334155">{html.escape(str(row.channel_name))}</text>'
            f'<rect x="240" y="{y}" width="{width}" height="26" rx="4" fill="#2563eb"/>'
            f'<text x="{250 + width}" y="{y + 20}" font-size="14" fill="#0f172a">{_money(float(row.spend))}</text>'
        )
    spend = float(channel["spend"].sum()) if "spend" in channel else 0.0
    revenue = float(channel["booked_revenue"].sum()) if "booked_revenue" in channel else 0.0
    margin = float(channel["gross_margin"].sum()) if "gross_margin" in channel else 0.0
    roas = revenue / spend if spend else 0.0
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f8fafc"/>
  <rect x="40" y="34" width="1200" height="652" rx="10" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="70" y="82" font-size="28" font-weight="700" fill="#0f172a">Executive Marketing Overview</text>
  <text x="70" y="112" font-size="15" fill="#64748b">Spend, revenue, margin, and channel efficiency generated from local release marts.</text>
  <rect x="70" y="132" width="205" height="82" rx="8" fill="#eff6ff" stroke="#bfdbfe"/>
  <text x="90" y="162" font-size="13" fill="#475569">Spend</text><text x="90" y="194" font-size="24" font-weight="700" fill="#0f172a">{_money(spend)}</text>
  <rect x="300" y="132" width="205" height="82" rx="8" fill="#f0fdf4" stroke="#bbf7d0"/>
  <text x="320" y="162" font-size="13" fill="#475569">Booked Revenue</text><text x="320" y="194" font-size="24" font-weight="700" fill="#0f172a">{_money(revenue)}</text>
  <rect x="530" y="132" width="205" height="82" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>
  <text x="550" y="162" font-size="13" fill="#475569">Gross Margin</text><text x="550" y="194" font-size="24" font-weight="700" fill="#0f172a">{_money(margin)}</text>
  <rect x="760" y="132" width="205" height="82" rx="8" fill="#fff7ed" stroke="#fed7aa"/>
  <text x="780" y="162" font-size="13" fill="#475569">ROAS</text><text x="780" y="194" font-size="24" font-weight="700" fill="#0f172a">{roas:.2f}x</text>
  <text x="70" y="260" font-size="20" font-weight="700" fill="#0f172a">Top Channel Spend</text>
  {''.join(rows)}
  <rect x="720" y="260" width="445" height="310" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="748" y="300" font-size="18" font-weight="700" fill="#0f172a">Trend Preview</text>
  <polyline points="760,500 820,470 880,486 940,420 1000,450 1060,386 1120,360" fill="none" stroke="#2563eb" stroke-width="4"/>
  <polyline points="760,526 820,512 880,494 940,470 1000,448 1060,422 1120,398" fill="none" stroke="#16a34a" stroke-width="4"/>
  <text x="748" y="612" font-size="14" fill="#64748b">Blue: spend. Green: revenue. Full interactive version runs in Streamlit.</text>
</svg>"""


def _governance_dashboard_svg(action_center: pd.DataFrame) -> str:
    priority_counts = action_center["priority"].value_counts().to_dict() if "priority" in action_center else {}
    p0 = int(priority_counts.get("P0", 0))
    p1 = int(priority_counts.get("P1", 0))
    p2 = int(priority_counts.get("P2", 0))
    rows = []
    for index, row in enumerate(action_center.head(7).itertuples(index=False), start=0):
        y = 230 + index * 42
        priority = html.escape(str(getattr(row, "priority", "")))
        owner = html.escape(str(getattr(row, "owner_team", "")))
        action = html.escape(str(getattr(row, "recommended_action", "")))[:82]
        rows.append(
            f'<text x="82" y="{y}" font-size="14" fill="#0f172a">{priority}</text>'
            f'<text x="150" y="{y}" font-size="14" fill="#334155">{owner}</text>'
            f'<text x="345" y="{y}" font-size="14" fill="#334155">{action}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f8fafc"/>
  <rect x="40" y="34" width="1200" height="652" rx="10" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="70" y="82" font-size="28" font-weight="700" fill="#0f172a">Governance and Action Center</text>
  <text x="70" y="112" font-size="15" fill="#64748b">Operational owners, certified KPI checks, privacy controls, and source health.</text>
  <rect x="70" y="140" width="190" height="78" rx="8" fill="#fef2f2" stroke="#fecaca"/>
  <text x="92" y="170" font-size="13" fill="#475569">P0 Actions</text><text x="92" y="199" font-size="25" font-weight="700" fill="#991b1b">{p0}</text>
  <rect x="286" y="140" width="190" height="78" rx="8" fill="#fff7ed" stroke="#fed7aa"/>
  <text x="308" y="170" font-size="13" fill="#475569">P1 Actions</text><text x="308" y="199" font-size="25" font-weight="700" fill="#9a3412">{p1}</text>
  <rect x="502" y="140" width="190" height="78" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>
  <text x="524" y="170" font-size="13" fill="#475569">P2 Actions</text><text x="524" y="199" font-size="25" font-weight="700" fill="#334155">{p2}</text>
  <text x="70" y="270" font-size="13" font-weight="700" fill="#475569">Priority</text>
  <text x="150" y="270" font-size="13" font-weight="700" fill="#475569">Owner Team</text>
  <text x="345" y="270" font-size="13" font-weight="700" fill="#475569">Recommended Action</text>
  {''.join(rows)}
  <rect x="910" y="160" width="255" height="340" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>
  <text x="938" y="205" font-size="18" font-weight="700" fill="#0f172a">Release Controls</text>
  <text x="938" y="250" font-size="15" fill="#334155">Classification catalog</text>
  <text x="938" y="290" font-size="15" fill="#334155">Access policy matrix</text>
  <text x="938" y="330" font-size="15" fill="#334155">Retention dry run</text>
  <text x="938" y="370" font-size="15" fill="#334155">Certified KPI catalog</text>
  <text x="938" y="410" font-size="15" fill="#334155">BI release packet</text>
</svg>"""


def _observability_dashboard_svg(source_health: pd.DataFrame, quality: pd.DataFrame) -> str:
    source_count = int(len(source_health))
    rejected_rows = int(quality["rejected_count"].sum()) if "rejected_count" in quality else 0
    failed_files = int((quality["status"] == "failed").sum()) if "status" in quality else 0
    rows = []
    for index, row in enumerate(source_health.head(8).itertuples(index=False), start=0):
        y = 252 + index * 38
        source = html.escape(str(getattr(row, "source_system", "")))
        status = html.escape(str(getattr(row, "source_health_status", getattr(row, "status", ""))))
        count = html.escape(str(getattr(row, "rows", getattr(row, "row_count", ""))))
        rows.append(
            f'<text x="82" y="{y}" font-size="14" fill="#0f172a">{source}</text>'
            f'<text x="360" y="{y}" font-size="14" fill="#334155">{status}</text>'
            f'<text x="520" y="{y}" font-size="14" fill="#334155">{count}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f8fafc"/>
  <rect x="40" y="34" width="1200" height="652" rx="10" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="70" y="82" font-size="28" font-weight="700" fill="#0f172a">Data Quality and Observability</text>
  <text x="70" y="112" font-size="15" fill="#64748b">Source health, rejected records, validation failures, and operational readiness.</text>
  <rect x="70" y="140" width="210" height="78" rx="8" fill="#eff6ff" stroke="#bfdbfe"/>
  <text x="92" y="170" font-size="13" fill="#475569">Sources Monitored</text><text x="92" y="199" font-size="25" font-weight="700" fill="#0f172a">{source_count}</text>
  <rect x="304" y="140" width="210" height="78" rx="8" fill="#fff7ed" stroke="#fed7aa"/>
  <text x="326" y="170" font-size="13" fill="#475569">Rejected Rows</text><text x="326" y="199" font-size="25" font-weight="700" fill="#0f172a">{rejected_rows}</text>
  <rect x="538" y="140" width="210" height="78" rx="8" fill="#fef2f2" stroke="#fecaca"/>
  <text x="560" y="170" font-size="13" fill="#475569">Failed Files</text><text x="560" y="199" font-size="25" font-weight="700" fill="#0f172a">{failed_files}</text>
  <text x="70" y="250" font-size="13" font-weight="700" fill="#475569">Source</text>
  <text x="360" y="250" font-size="13" font-weight="700" fill="#475569">Health Status</text>
  <text x="520" y="250" font-size="13" font-weight="700" fill="#475569">Rows</text>
  {''.join(rows)}
  <rect x="850" y="170" width="300" height="330" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>
  <text x="880" y="214" font-size="18" font-weight="700" fill="#0f172a">Monitored Signals</text>
  <text x="880" y="260" font-size="15" fill="#334155">Freshness windows</text>
  <text x="880" y="300" font-size="15" fill="#334155">Schema drift</text>
  <text x="880" y="340" font-size="15" fill="#334155">Rejected records</text>
  <text x="880" y="380" font-size="15" fill="#334155">Contract checks</text>
  <text x="880" y="420" font-size="15" fill="#334155">Watermark readiness</text>
</svg>"""


def _money(value: float) -> str:
    return f"${value:,.0f}"


def main() -> None:
    print(json.dumps(generate_evidence(), indent=2))


if __name__ == "__main__":
    main()
