from pathlib import Path

from scripts.apply_retention_policy import build_retention_actions
from scripts.pii_discovery import classify_field, discover_fields


def test_pii_classifier_detects_identifiers_and_sensitive_values() -> None:
    assert classify_field("customer_id")[0] == "direct_identifier"
    assert classify_field("gross_margin")[0] == "commercially_sensitive"
    assert classify_field("utm_campaign_id")[0] == "attribution_identifier"
    assert classify_field("region")[0] == "location"
    assert classify_field("ordinary_metric")[0] == "not_sensitive"


def test_pii_discovery_scans_temp_schema(tmp_path: Path) -> None:
    schema = tmp_path / "model.sql"
    schema.write_text(
        "select customer_id, lead_id, gross_margin, region, safe_metric from source_table",
        encoding="utf-8",
    )

    report = discover_fields([tmp_path])

    assert {"customer_id", "lead_id", "gross_margin", "region"}.issubset(set(report["field_name"]))
    assert "safe_metric" not in set(report["field_name"])


def test_retention_dry_run_has_non_destructive_execution_mode() -> None:
    actions = build_retention_actions()

    assert not actions.empty
    assert actions["execution_mode"].eq("dry_run").all()
    assert actions["planned_sql_pattern"].str.startswith("--").all()
    assert "customer_dimension_1095_days" in set(actions["retention_policy"])


def test_security_views_define_masked_surfaces() -> None:
    sql_path = Path("warehouse/postgres/views/security_views.sql")
    sql = sql_path.read_text(encoding="utf-8")

    assert "security.masked_dim_customer" in sql
    assert "security.masked_fact_leads" in sql
    assert "security.executive_channel_performance" in sql
    assert "sha256" in sql
    assert "grant select" in sql
