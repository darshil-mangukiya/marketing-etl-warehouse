from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "governance" / "generated"
REPORT_DIR = PROJECT_ROOT / "reports" / "generated"


def data_classification_catalog() -> pd.DataFrame:
    rows = [
        {
            "asset_name": "raw.crm_leads",
            "layer": "raw",
            "asset_type": "source_table",
            "description": "CRM lead records with lead source, assigned rep, qualification stage, region, customer identifier, and attribution ID.",
            "owner_team": "sales_operations",
            "data_steward": "revenue_operations",
            "classification": "confidential",
            "pii_level": "direct_identifier",
            "sensitive_fields": "lead_id, customer_id, assigned_rep, attribution_id",
            "primary_key": "lead_id",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, sales_operations",
            "masked_roles": "bi_developer, marketing_leadership",
            "masking_policy": "Hash lead_id and customer_id; hide assigned_rep outside sales operations.",
            "retention_policy": "raw_customer_touchpoint_730_days",
        },
        {
            "asset_name": "raw.sales_conversions",
            "layer": "raw",
            "asset_type": "source_table",
            "description": "Closed-won sales conversions with deal value, gross margin, product, conversion date, customer ID, and lead ID.",
            "owner_team": "revenue_operations",
            "data_steward": "growth_finance",
            "classification": "restricted",
            "pii_level": "direct_identifier",
            "sensitive_fields": "conversion_id, lead_id, customer_id, deal_value, gross_margin",
            "primary_key": "conversion_id",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, revenue_operations, growth_finance",
            "masked_roles": "bi_developer, marketing_leadership",
            "masking_policy": "Expose aggregated revenue and margin in marts; restrict row-level customer IDs.",
            "retention_policy": "revenue_fact_1095_days",
        },
        {
            "asset_name": "raw.website_analytics",
            "layer": "raw",
            "asset_type": "source_table",
            "description": "Session-level web analytics with device, geography, traffic source, UTM campaign ID, and bounce behavior.",
            "owner_team": "growth_marketing",
            "data_steward": "analytics_engineering",
            "classification": "confidential",
            "pii_level": "pseudonymous",
            "sensitive_fields": "session_id, utm_campaign_id",
            "primary_key": "session_id",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, bi_developer",
            "masked_roles": "marketing_leadership",
            "masking_policy": "Aggregate session-level records before executive reporting.",
            "retention_policy": "web_event_730_days",
        },
        {
            "asset_name": "warehouse.dim_customer",
            "layer": "warehouse",
            "asset_type": "dimension",
            "description": "Customer and lead identity dimension prepared for LTV and segmentation.",
            "owner_team": "analytics_engineering",
            "data_steward": "revenue_operations",
            "classification": "restricted",
            "pii_level": "direct_identifier",
            "sensitive_fields": "customer_id, lead_id",
            "primary_key": "customer_key",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, revenue_operations",
            "masked_roles": "bi_developer, marketing_leadership, external_auditor",
            "masking_policy": "Use surrogate keys in BI exports; suppress natural IDs for broad audiences.",
            "retention_policy": "customer_dimension_1095_days",
        },
        {
            "asset_name": "warehouse.fact_revenue",
            "layer": "warehouse",
            "asset_type": "fact",
            "description": "Revenue and margin fact table used for executive KPIs, customer value, and attribution reconciliation.",
            "owner_team": "growth_finance",
            "data_steward": "revenue_operations",
            "classification": "restricted",
            "pii_level": "commercially_sensitive",
            "sensitive_fields": "deal_value, gross_margin, customer_key",
            "primary_key": "conversion_key",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, growth_finance, revenue_operations",
            "masked_roles": "bi_developer, marketing_leadership",
            "masking_policy": "Use aggregated revenue and margin in marts; hide row-level deal values from broad dashboard roles.",
            "retention_policy": "revenue_fact_1095_days",
        },
        {
            "asset_name": "mart_channel_performance",
            "layer": "mart",
            "asset_type": "reporting_mart",
            "description": "Channel-level executive mart for spend, revenue, gross margin, ROAS, CAC, and lead funnel KPIs.",
            "owner_team": "revenue_operations",
            "data_steward": "analytics_engineering",
            "classification": "internal",
            "pii_level": "aggregated",
            "sensitive_fields": "booked_revenue, gross_margin",
            "primary_key": "reporting_month, normalized_channel",
            "refresh_cadence": "daily",
            "allowed_roles": "bi_developer, marketing_leadership, growth_finance, analytics_engineer",
            "masked_roles": "external_auditor",
            "masking_policy": "Suppress low-volume slices if exported externally.",
            "retention_policy": "aggregate_mart_1825_days",
        },
        {
            "asset_name": "mart_customer_value",
            "layer": "mart",
            "asset_type": "reporting_mart",
            "description": "Customer LTV and margin mart used for customer segment analysis.",
            "owner_team": "revenue_operations",
            "data_steward": "analytics_engineering",
            "classification": "confidential",
            "pii_level": "pseudonymous",
            "sensitive_fields": "customer_id, lifetime_revenue, lifetime_margin",
            "primary_key": "customer_id",
            "refresh_cadence": "daily",
            "allowed_roles": "analytics_engineer, revenue_operations, growth_finance",
            "masked_roles": "bi_developer, marketing_leadership",
            "masking_policy": "Expose segment rollups in executive dashboards; restrict customer-level exports.",
            "retention_policy": "customer_value_1095_days",
        },
        {
            "asset_name": "mart_action_center",
            "layer": "mart",
            "asset_type": "operational_mart",
            "description": "Owned action queue for campaign optimization, source reliability, data quality, planning, and anomaly work.",
            "owner_team": "marketing_operations",
            "data_steward": "data_product_owner",
            "classification": "internal",
            "pii_level": "none",
            "sensitive_fields": "business_impact, evidence_metric",
            "primary_key": "action_id",
            "refresh_cadence": "daily",
            "allowed_roles": "data_engineer, analytics_engineer, bi_developer, marketing_leadership, growth_finance",
            "masked_roles": "external_auditor",
            "masking_policy": "Remove owner-team names and business-impact values for external sharing.",
            "retention_policy": "operational_action_365_days",
        },
        {
            "asset_name": "mart_semantic_kpi_governance",
            "layer": "semantic",
            "asset_type": "governance_mart",
            "description": "Certified KPI definitions with formulas, owners, guardrails, source marts, dashboard pages, and dependencies.",
            "owner_team": "bi_development",
            "data_steward": "revenue_operations",
            "classification": "internal",
            "pii_level": "none",
            "sensitive_fields": "none",
            "primary_key": "kpi_name",
            "refresh_cadence": "on release",
            "allowed_roles": "all_internal_roles",
            "masked_roles": "none",
            "masking_policy": "No masking required.",
            "retention_policy": "governance_reference_indefinite",
        },
        {
            "asset_name": "mart_data_product_scorecard",
            "layer": "semantic",
            "asset_type": "governance_mart",
            "description": "Operating scorecard for source reliability, quality, attribution, action management, planning, and executive confidence.",
            "owner_team": "data_product_owner",
            "data_steward": "analytics_engineering",
            "classification": "internal",
            "pii_level": "none",
            "sensitive_fields": "evidence, next_action",
            "primary_key": "scorecard_domain",
            "refresh_cadence": "daily",
            "allowed_roles": "all_internal_roles",
            "masked_roles": "external_auditor",
            "masking_policy": "Share domain-level status externally; remove operational evidence text.",
            "retention_policy": "governance_scorecard_730_days",
        },
    ]
    return pd.DataFrame(rows)


def access_policy_matrix() -> pd.DataFrame:
    rows = [
        ("data_engineer", "raw", "admin", "Needed to operate ingestion, replay, rejects, and source contracts."),
        ("data_engineer", "warehouse", "admin", "Needed to operate warehouse loads, indexes, and recovery."),
        ("data_engineer", "mart", "read", "Needed for incident investigation and data validation."),
        ("analytics_engineer", "raw", "read_masked", "Needed for debugging, but natural identifiers should be masked by default."),
        ("analytics_engineer", "warehouse", "write_model", "Owns dbt models, tests, and semantic transformations."),
        ("analytics_engineer", "mart", "write_model", "Owns mart definitions and certified KPI dependencies."),
        ("bi_developer", "raw", "none", "BI developers should not consume raw customer or event-level data."),
        ("bi_developer", "warehouse", "read_masked", "Allowed for model validation when surrogate keys and masks are applied."),
        ("bi_developer", "mart", "read", "Primary dashboard and semantic-model surface."),
        ("marketing_leadership", "raw", "none", "Leadership consumes governed aggregate marts only."),
        ("marketing_leadership", "warehouse", "none", "Warehouse tables are not a self-service surface."),
        ("marketing_leadership", "mart", "read_aggregate", "Can view executive, channel, campaign, planning, and governance marts."),
        ("growth_finance", "raw", "none", "Finance should not use raw source records for reporting."),
        ("growth_finance", "warehouse", "read_sensitive", "Can inspect revenue and margin facts for planning control."),
        ("growth_finance", "mart", "read", "Can consume budget, scenario, forecast, and target attainment marts."),
        ("sales_operations", "raw", "read_masked", "Can validate CRM source issues and lead handoff quality."),
        ("sales_operations", "warehouse", "read_masked", "Can inspect customer and lead dimensions for operational QA."),
        ("sales_operations", "mart", "read", "Can consume funnel, conversion lag, and customer segment marts."),
        ("external_auditor", "raw", "none", "No raw-system access in the local platform design."),
        ("external_auditor", "warehouse", "none", "No direct warehouse access in the local platform design."),
        ("external_auditor", "mart", "read_redacted", "Can receive redacted aggregate evidence exports only."),
    ]
    return pd.DataFrame(rows, columns=["role_name", "data_layer", "access_level", "access_rationale"])


def retention_policy_matrix() -> pd.DataFrame:
    rows = [
        ("raw_customer_touchpoint_730_days", "raw CRM and attribution records", 730, "anonymize", "Supports funnel replay while limiting direct-identifier retention."),
        ("web_event_730_days", "raw website session events", 730, "delete", "Session-level data is retained long enough for seasonality and attribution review."),
        ("revenue_fact_1095_days", "sales conversion and revenue facts", 1095, "archive_then_delete", "Three-year history supports LTV and planning comparisons."),
        ("customer_dimension_1095_days", "customer identity dimension", 1095, "anonymize", "Preserve segment analytics while removing natural identifiers."),
        ("customer_value_1095_days", "customer-level LTV marts", 1095, "aggregate_then_delete", "Retain customer-level LTV only while analytically necessary."),
        ("aggregate_mart_1825_days", "aggregate BI marts", 1825, "archive", "Aggregated reporting marts are useful for long-term executive trend analysis."),
        ("operational_action_365_days", "action center rows", 365, "archive_then_delete", "Operational action history supports postmortems without growing indefinitely."),
        ("governance_scorecard_730_days", "data product scorecard rows", 730, "archive", "Retain enough history to show operating maturity over time."),
        ("governance_reference_indefinite", "KPI definitions and policy references", 0, "retain_until_superseded", "Definitions should remain versioned as governance evidence."),
    ]
    return pd.DataFrame(
        rows,
        columns=["retention_policy", "applies_to", "retention_days", "disposition_action", "business_reason"],
    )


def certification_evidence(project_root: Path = PROJECT_ROOT) -> dict:
    required_artifacts = [
        "data/exports/demo_mart_manifest.json",
        "data/exports/demo_mart_data_product_scorecard.csv",
        "data/exports/demo_mart_semantic_kpi_governance.csv",
        "data/exports/demo_mart_action_center.csv",
        "reports/generated/executive_planning_report.html",
        "semantic_layer/powerbi_tmdl/semantic_model_manifest.json",
        "docs/data_quality_framework.md",
        "docs/dashboard_outputs.md",
    ]
    artifact_results = []
    for relative_path in required_artifacts:
        path = project_root / relative_path
        artifact_results.append(
            {
                "artifact": relative_path,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )

    demo_manifest_path = project_root / "data" / "exports" / "demo_mart_manifest.json"
    semantic_manifest_path = project_root / "semantic_layer" / "powerbi_tmdl" / "semantic_model_manifest.json"
    demo_manifest = json.loads(demo_manifest_path.read_text(encoding="utf-8")) if demo_manifest_path.exists() else {}
    semantic_manifest = (
        json.loads(semantic_manifest_path.read_text(encoding="utf-8")) if semantic_manifest_path.exists() else {}
    )
    passed_artifacts = sum(1 for result in artifact_results if result["exists"])
    status = "certified" if passed_artifacts == len(artifact_results) else "incomplete"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release_status": status,
        "artifact_pass_rate": passed_artifacts / len(artifact_results),
        "required_artifact_count": len(artifact_results),
        "available_artifact_count": passed_artifacts,
        "demo_mart_count": len(demo_manifest.get("tables", [])),
        "semantic_table_count": semantic_manifest.get("table_count", 0),
        "semantic_measure_count": semantic_manifest.get("measure_count", 0),
        "artifacts": artifact_results,
    }


def generate_governance_pack(project_root: Path = PROJECT_ROOT) -> dict:
    output_dir = project_root / "governance" / "generated"
    report_dir = project_root / "reports" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    catalog = data_classification_catalog()
    access = access_policy_matrix()
    retention = retention_policy_matrix()
    evidence = certification_evidence(project_root)

    catalog_path = output_dir / "data_classification_catalog.csv"
    access_path = output_dir / "access_policy_matrix.csv"
    retention_path = output_dir / "retention_policy_matrix.csv"
    evidence_path = output_dir / "bi_release_certification.json"
    markdown_path = output_dir / "bi_release_certification.md"
    html_path = report_dir / "governance_release_packet.html"

    catalog.to_csv(catalog_path, index=False)
    access.to_csv(access_path, index=False)
    retention.to_csv(retention_path, index=False)
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(catalog, access, retention, evidence), encoding="utf-8")
    html_path.write_text(_render_html(catalog, access, retention, evidence), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": evidence["release_status"],
        "outputs": {
            "data_classification_catalog": str(catalog_path.relative_to(project_root)),
            "access_policy_matrix": str(access_path.relative_to(project_root)),
            "retention_policy_matrix": str(retention_path.relative_to(project_root)),
            "bi_release_certification_json": str(evidence_path.relative_to(project_root)),
            "bi_release_certification_markdown": str(markdown_path.relative_to(project_root)),
            "governance_release_packet": str(html_path.relative_to(project_root)),
        },
        "classified_asset_count": len(catalog),
        "restricted_asset_count": int(catalog["classification"].isin(["restricted", "confidential"]).sum()),
        "access_policy_count": len(access),
        "retention_policy_count": len(retention),
        "artifact_pass_rate": evidence["artifact_pass_rate"],
    }
    (output_dir / "governance_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _render_markdown(
    catalog: pd.DataFrame,
    access: pd.DataFrame,
    retention: pd.DataFrame,
    evidence: dict,
) -> str:
    restricted = catalog[catalog["classification"].isin(["restricted", "confidential"])]
    direct_pii = catalog[catalog["pii_level"].eq("direct_identifier")]
    artifact_lines = [
        f"- [{'x' if item['exists'] else ' '}] `{item['artifact']}` ({item['size_bytes']:,} bytes)"
        for item in evidence["artifacts"]
    ]
    return f"""# BI Release Certification and Governance Packet

Generated: `{datetime.now(timezone.utc).isoformat()}`

Release status: `{evidence['release_status']}`

| Control | Value |
|---|---:|
| Artifact Pass Rate | {evidence['artifact_pass_rate']:.0%} |
| Demo Mart Count | {evidence['demo_mart_count']:,} |
| Semantic Table Count | {evidence['semantic_table_count']:,} |
| Semantic Measure Count | {evidence['semantic_measure_count']:,} |
| Classified Assets | {len(catalog):,} |
| Restricted or Confidential Assets | {len(restricted):,} |
| Direct-Identifier Assets | {len(direct_pii):,} |
| Access Policy Rows | {len(access):,} |
| Retention Policies | {len(retention):,} |

## Required Artifacts

{chr(10).join(artifact_lines)}

## Privacy Controls

- Direct identifiers are restricted to data engineering, analytics engineering, sales operations, revenue operations, or finance depending on business need.
- BI and leadership surfaces consume masked, surrogate-keyed, or aggregate marts.
- Customer-level exports are restricted; executive dashboards should use channel, segment, region, or product rollups.
- External audit sharing uses redacted aggregate evidence only.

## Release Decision

The release is marked `{evidence['release_status']}` when all required data, dashboard, semantic, governance, and documentation artifacts exist.
"""


def _render_html(
    catalog: pd.DataFrame,
    access: pd.DataFrame,
    retention: pd.DataFrame,
    evidence: dict,
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Governance Release Packet</title>
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
    .note {{ background: #f0fdf4; border-left: 5px solid #16a34a; padding: 14px 18px; margin: 18px 0; }}
  </style>
</head>
<body>
  <h1>Governance Release Packet</h1>
  <p>Generated {html.escape(generated_at)}. This packet documents privacy controls, access roles, retention policies, and BI release certification evidence.</p>
  <div class="grid">
    {_card("Release Status", str(evidence["release_status"]).title())}
    {_card("Artifact Pass Rate", f"{evidence['artifact_pass_rate']:.0%}")}
    {_card("Demo Marts", f"{evidence['demo_mart_count']:,}")}
    {_card("Semantic Measures", f"{evidence['semantic_measure_count']:,}")}
    {_card("Classified Assets", f"{len(catalog):,}")}
    {_card("Restricted Assets", f"{catalog['classification'].isin(['restricted', 'confidential']).sum():,}")}
    {_card("Access Policies", f"{len(access):,}")}
    {_card("Retention Policies", f"{len(retention):,}")}
  </div>
  <div class="note">Leadership and BI users consume governed aggregate marts; raw direct identifiers stay restricted to operational roles.</div>

  <h2>Required Assets</h2>
  <table><thead><tr><th>Artifact</th><th>Exists</th><th>Size Bytes</th></tr></thead><tbody>{_artifact_rows(evidence)}</tbody></table>

  <h2>Data Classification Catalog</h2>
  <table><thead><tr><th>Asset</th><th>Layer</th><th>Classification</th><th>PII Level</th><th>Owner</th><th>Masking Policy</th></tr></thead><tbody>{_table_rows(catalog, ["asset_name", "layer", "classification", "pii_level", "owner_team", "masking_policy"])}</tbody></table>

  <h2>Access Policy Matrix</h2>
  <table><thead><tr><th>Role</th><th>Layer</th><th>Access</th><th>Rationale</th></tr></thead><tbody>{_table_rows(access, ["role_name", "data_layer", "access_level", "access_rationale"])}</tbody></table>

  <h2>Retention Policy Matrix</h2>
  <table><thead><tr><th>Policy</th><th>Applies To</th><th>Days</th><th>Disposition</th><th>Reason</th></tr></thead><tbody>{_table_rows(retention, ["retention_policy", "applies_to", "retention_days", "disposition_action", "business_reason"])}</tbody></table>
</body>
</html>"""


def _card(label: str, value: str) -> str:
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{html.escape(value)}</div></div>'


def _artifact_rows(evidence: dict) -> str:
    rows = []
    for item in evidence["artifacts"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item['artifact']))}</td>"
            f"<td>{'yes' if item['exists'] else 'no'}</td>"
            f"<td>{int(item['size_bytes']):,}</td>"
            "</tr>"
        )
    return "".join(rows)


def _table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return f'<tr><td colspan="{len(columns)}">No rows available.</td></tr>'
    rows = []
    for _, row in frame.iterrows():
        cells = [f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns]
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(rows)


def main() -> None:
    print(json.dumps(generate_governance_pack(), indent=2))


if __name__ == "__main__":
    main()
