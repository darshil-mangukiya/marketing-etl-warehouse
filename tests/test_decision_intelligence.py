import pytest

from data_sources.generators import run_generation
from scripts.generate_decision_intelligence import build_reconciliation, generate


@pytest.fixture(scope="module", autouse=True)
def generated_source_manifest() -> None:
    run_generation(profile="smoke", clean=True)


def test_source_to_target_reconciliation_has_no_failed_checks() -> None:
    result = build_reconciliation()

    assert result["check_count"] >= 30
    assert result["failed_count"] == 0
    assert result["overall_status"] == "PASS"


def test_decision_intelligence_generation_produces_governed_outputs() -> None:
    result = generate()

    assert result["scenario_rows"] > 0
    assert result["reconciliation_status"] == "PASS"
    assert result["packet_output"] == "artifacts/decision_intelligence/latest_insight_packet.json"
