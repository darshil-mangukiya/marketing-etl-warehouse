from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_json(path: Path, default: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def build_scorecard() -> dict:
    quality = _load_json(PROJECT_ROOT / "data" / "quality_reports" / "latest_quality_summary.json", {})
    ge = _load_json(PROJECT_ROOT / "data" / "quality_reports" / "great_expectations" / "marketing_raw_checkpoint_result.json", {})
    contracts = _load_json(PROJECT_ROOT / "data" / "quality_reports" / "contracts" / "contract_check_results.json", {})
    catalog = _load_json(PROJECT_ROOT / "catalog" / "generated" / "data_catalog.json", {})
    local_gate = _load_json(PROJECT_ROOT / "local_ci" / "latest_quality_gate.json", {})
    benchmark = _load_json(PROJECT_ROOT / "benchmarks" / "results" / "pipeline_benchmark_latest.json", {})

    scorecard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": _overall_status([quality, ge, contracts, local_gate, benchmark]),
        "quality": {
            "row_count": quality.get("row_count"),
            "rejected_count": quality.get("rejected_count"),
            "quality_gate": _quality_gate(quality),
        },
        "great_expectations": {
            "quality_gate": ge.get("quality_gate"),
            "evaluated_files": ge.get("statistics", {}).get("evaluated_files"),
            "evaluated_rows": ge.get("statistics", {}).get("evaluated_rows"),
        },
        "contracts": {
            "status": contracts.get("status"),
            "issue_count": contracts.get("issue_count"),
        },
        "catalog": {
            "models": catalog.get("counts", {}).get("models"),
            "sources": catalog.get("counts", {}).get("sources"),
            "lineage_edges": catalog.get("counts", {}).get("lineage_edges"),
            "fields": catalog.get("counts", {}).get("fields"),
        },
        "local_quality_gate": {
            "status": local_gate.get("status"),
            "checks": len(local_gate.get("checks", [])),
        },
        "benchmark": {
            "status": benchmark.get("status"),
            "total_elapsed_seconds": benchmark.get("total_elapsed_seconds"),
        },
    }
    output_dir = PROJECT_ROOT / "ops" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "operational_scorecard.json").write_text(json.dumps(scorecard, indent=2), encoding="utf-8")
    (output_dir / "operational_scorecard.md").write_text(_scorecard_markdown(scorecard), encoding="utf-8")
    return scorecard


def _quality_gate(quality: dict) -> str | None:
    if not quality:
        return None
    row_count = quality.get("row_count") or 0
    rejected_count = quality.get("rejected_count") or 0
    rejected_rate = rejected_count / row_count if row_count else 0
    return "pass" if rejected_rate < 0.05 else "quarantine"


def _overall_status(items: list[dict]) -> str:
    failed = [item for item in items if item.get("status") == "failed"]
    quarantined = [item for item in items if item.get("quality_gate") == "quarantine"]
    return "watch" if failed or quarantined else "healthy"


def _scorecard_markdown(scorecard: dict) -> str:
    return f"""# Operational Scorecard

Generated: `{scorecard['generated_at']}`

Overall status: **{scorecard['overall_status']}**

| Area | Signal |
|---|---|
| Quality rows | {scorecard['quality']['row_count']} |
| Rejected rows | {scorecard['quality']['rejected_count']} |
| GE quality gate | {scorecard['great_expectations']['quality_gate']} |
| Contract status | {scorecard['contracts']['status']} |
| Catalog models | {scorecard['catalog']['models']} |
| Lineage edges | {scorecard['catalog']['lineage_edges']} |
| Local quality gate | {scorecard['local_quality_gate']['status']} |
| Benchmark status | {scorecard['benchmark']['status']} |
"""


def main() -> None:
    print(json.dumps(build_scorecard(), indent=2))


if __name__ == "__main__":
    main()
