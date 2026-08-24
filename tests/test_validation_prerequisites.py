import json

import pytest

from ingestion import prerequisites
from scripts import generate_final_validation_assets


def _valid_summary(rows: int = 10) -> dict:
    return {
        "batch_id": "batch_test",
        "status": "completed",
        "completed_at": "2026-08-22T00:00:00+00:00",
        "sources": {
            "google_ads": {
                "files": 1,
                "rows": rows,
                "accepted": rows,
                "rejected": 0,
                "failed": 0,
                "skipped": 0,
            }
        },
    }


def test_existing_ingestion_summary_is_reused(tmp_path, monkeypatch) -> None:
    target = tmp_path / "latest_ingestion_summary.json"
    target.write_text(json.dumps(_valid_summary()))

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("generator must not run for a valid existing prerequisite")

    monkeypatch.setattr(prerequisites, "_build_ingestion_summary", fail_if_called)

    assert prerequisites.ensure_ingestion_summary(tmp_path, target)["batch_id"] == "batch_test"


def test_missing_ingestion_summary_is_generated_atomically(tmp_path, monkeypatch) -> None:
    target = tmp_path / "data/logs/latest_ingestion_summary.json"
    monkeypatch.setattr(
        prerequisites,
        "_build_ingestion_summary",
        lambda _project_root, _temporary_root: _valid_summary(),
    )

    result = prerequisites.ensure_ingestion_summary(tmp_path, target)

    assert result["status"] == "completed"
    assert json.loads(target.read_text()) == result
    assert not target.with_suffix(".json.tmp").exists()


def test_invalid_ingestion_summary_is_rebuilt(tmp_path, monkeypatch) -> None:
    target = tmp_path / "latest_ingestion_summary.json"
    target.write_text('{"status": "running", "sources": {}}')
    monkeypatch.setattr(
        prerequisites,
        "_build_ingestion_summary",
        lambda _project_root, _temporary_root: _valid_summary(),
    )

    assert prerequisites.ensure_ingestion_summary(tmp_path, target)["status"] == "completed"


def test_ingestion_summary_generation_failure_blocks_validation(tmp_path, monkeypatch) -> None:
    target = tmp_path / "latest_ingestion_summary.json"

    def fail_generation(*_args, **_kwargs):
        raise OSError("synthetic generator unavailable")

    monkeypatch.setattr(prerequisites, "_build_ingestion_summary", fail_generation)

    with pytest.raises(RuntimeError, match="Decision-intelligence and BI validation are blocked"):
        prerequisites.ensure_ingestion_summary(tmp_path, target)
    assert not target.exists()


def test_repeated_ingestion_summary_preparation_is_idempotent(tmp_path, monkeypatch) -> None:
    target = tmp_path / "latest_ingestion_summary.json"
    calls = 0

    def build_once(_project_root, _temporary_root):
        nonlocal calls
        calls += 1
        return _valid_summary()

    monkeypatch.setattr(prerequisites, "_build_ingestion_summary", build_once)

    first = prerequisites.ensure_ingestion_summary(tmp_path, target)
    second = prerequisites.ensure_ingestion_summary(tmp_path, target)

    assert first == second
    assert calls == 1


def test_bi_validator_receives_prepared_ingestion_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        generate_final_validation_assets,
        "ensure_ingestion_summary",
        lambda _project_root: _valid_summary(rows=25),
    )

    reliability = generate_final_validation_assets.build_reliability()
    google_ads = next(row for row in reliability["sources"] if row["source"] == "google_ads")

    assert google_ads["observed_rows"] == 25
    assert google_ads["validation_status"] == "PASS"


def test_real_local_builder_produces_valid_bounded_summary(tmp_path) -> None:
    summary = prerequisites._build_ingestion_summary(tmp_path, tmp_path / "runtime")

    validated = prerequisites._validate_ingestion_summary(summary)
    assert validated["status"] == "completed"
    assert 2_500 <= validated["sources"]["google_ads"]["rows"] < 2_600
    assert 4_000 <= validated["sources"]["ga4_events"]["rows"] < 4_100
