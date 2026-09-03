import re
import zipfile
from pathlib import Path

from scripts.generate_final_validation_assets import (
    build_bi_validation,
    build_registry,
    build_reliability,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _xlsx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )


def test_enterprise_dictionary_has_required_sheets_and_exact_ids() -> None:
    path = PROJECT_ROOT / "governance/data_dictionary.xlsx"
    assert path.stat().st_size > 20_000
    text = _xlsx_text(path)
    for sheet in ("Source Fields", "Warehouse Fields", "KPIs", "Dimensions", "Governance - Ownership", "Coverage Summary"):
        assert f'name="{sheet}"' in text
    for identifier in ("SRC-GADS-001", "SRC-GA4-016", "SRC-RMAP-042", "WH-001", "WH-072", "KPI-001", "KPI-022"):
        assert identifier in text


def test_rtm_links_requirements_to_dictionary_field_ids() -> None:
    text = _xlsx_text(PROJECT_ROOT / "business_analysis/requirements_traceability_matrix.xlsx")
    assert "Data Dictionary / Field IDs" in text
    assert all(identifier in text for identifier in ("SRC-GADS-005", "WH-039", "KPI-014", "SRC-GA4-021", "WH-024"))


def test_bi_semantic_regression_contract_passes() -> None:
    result = build_bi_validation()
    assert result["status"] == "PASS"
    assert result["check_count"] == 27
    assert result["failed_count"] == 0
    checks = {check["check_id"]: check for check in result["checks"]}
    assert checks["BI-003"]["actual"] == 9
    assert checks["BI-003B"]["actual"] == 11
    assert checks["BI-002"]["actual"] == 59


def test_reliability_and_report_governance_are_bounded_and_truthful() -> None:
    reliability = build_reliability()
    registry = build_registry()
    assert reliability["source_count"] == 8
    assert {row["reliability_status"] for row in reliability["sources"]} <= {"FRESH", "WARNING", "BREACHED", "NOT APPLICABLE"}
    assert registry["asset_count"] == 6
    assert {row["certification_status"] for row in registry["assets"]} <= set(registry["allowed_statuses"])
    assert all("Power BI Service certification" not in row["certification_status"] for row in registry["assets"])


def test_performance_and_dax_audits_use_evidence_not_invented_benchmarks() -> None:
    performance = (PROJECT_ROOT / "docs/performance/bigquery_query_optimization.md").read_text()
    dax_doc = (PROJECT_ROOT / "docs/bi/dax_optimization.md").read_text()
    dax = (PROJECT_ROOT / "dashboards/powerbi/dax_measures.dax").read_text()
    assert all(value in performance for value in ("619", "587", "5.17%", "NOT MEASURED"))
    assert "zero measures changed" in dax_doc.lower()
    assert len(re.findall(r"^[A-Za-z0-9][^=\n]+?\s=", dax, flags=re.MULTILINE)) == 59


def test_lineage_covers_major_decision_metrics() -> None:
    lineage = (PROJECT_ROOT / "docs/lineage/kpi_lineage.md").read_text()
    assert "```mermaid" in lineage
    for term in ("ROAS", "CAC", "Funnel", "Attribution", "Target", "Scenario", "Live GA4"):
        assert term in lineage
