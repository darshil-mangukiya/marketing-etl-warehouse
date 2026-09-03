from pathlib import Path

from scripts.generate_governance_pack import (
    access_policy_matrix,
    certification_evidence,
    data_classification_catalog,
    retention_policy_matrix,
)


def test_data_classification_catalog_marks_sensitive_assets() -> None:
    catalog = data_classification_catalog()

    assert {"asset_name", "classification", "pii_level", "masking_policy", "retention_policy"}.issubset(catalog.columns)
    sensitive = catalog[catalog["pii_level"].isin(["direct_identifier", "pseudonymous", "commercially_sensitive"])]
    assert not sensitive.empty
    assert sensitive["masking_policy"].str.len().gt(10).all()
    assert "warehouse.dim_customer" in set(catalog["asset_name"])
    assert "mart_semantic_kpi_governance" in set(catalog["asset_name"])


def test_access_policy_prevents_raw_leadership_access() -> None:
    access = access_policy_matrix()

    leadership_raw = access[(access["role_name"].eq("marketing_leadership")) & (access["data_layer"].eq("raw"))]
    assert leadership_raw.iloc[0]["access_level"] == "none"
    assert access[(access["role_name"].eq("bi_developer")) & (access["data_layer"].eq("mart"))].iloc[0]["access_level"] == "read"
    assert "read_redacted" in set(access["access_level"])


def test_retention_policy_has_disposition_controls() -> None:
    retention = retention_policy_matrix()

    assert retention["retention_policy"].is_unique
    assert {"delete", "anonymize", "archive_then_delete", "aggregate_then_delete"}.intersection(
        set(retention["disposition_action"])
    )
    customer_policy = retention[retention["retention_policy"].eq("customer_dimension_1095_days")].iloc[0]
    assert customer_policy["disposition_action"] == "anonymize"


def test_certification_evidence_reports_missing_artifacts_for_empty_project(tmp_path: Path) -> None:
    evidence = certification_evidence(tmp_path)

    assert evidence["release_status"] == "incomplete"
    assert evidence["artifact_pass_rate"] == 0
    assert evidence["required_artifact_count"] == len(evidence["artifacts"])
