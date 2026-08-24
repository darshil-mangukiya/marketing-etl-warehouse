from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import PlatformConfig
from ingestion.file_io import read_frame

CONTRACT_PATH = PROJECT_ROOT / "contracts" / "source_contracts.yml"


@dataclass(frozen=True)
class ContractIssue:
    source_system: str
    rule_name: str
    severity: str
    failed_count: int
    detail: str


def load_contracts(path: Path = CONTRACT_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def discover_raw_files(config: PlatformConfig, source_system: str) -> list[Path]:
    root = config.data_lake_root / "raw" / f"source_system={source_system}"
    files: list[Path] = []
    for pattern in ("*.csv", "*.jsonl", "*.parquet"):
        files.extend(root.rglob(pattern))
    return sorted(files)


def validate_frame_against_contract(source_system: str, frame: pd.DataFrame, contract: dict) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    required_columns = contract.get("required_columns", {})
    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        issues.append(
            ContractIssue(
                source_system,
                "required_columns",
                "error",
                len(missing),
                f"Missing columns: {', '.join(missing)}",
            )
        )

    for column, expected_type in required_columns.items():
        if column not in frame.columns:
            continue
        invalid = _invalid_type_mask(frame[column], expected_type)
        if invalid.any():
            issues.append(
                ContractIssue(
                    source_system,
                    f"type_{column}_{expected_type}",
                    "warning",
                    int(invalid.sum()),
                    f"Column {column} has values that cannot be parsed as {expected_type}",
                )
            )

    primary_key = contract.get("primary_key", [])
    if primary_key and set(primary_key).issubset(frame.columns):
        duplicate_key = frame.duplicated(subset=primary_key, keep=False)
        if duplicate_key.any():
            issues.append(
                ContractIssue(
                    source_system,
                    "primary_key_unique",
                    "warning",
                    int(duplicate_key.sum()),
                    f"Duplicate rows for key {primary_key}",
                )
            )

    for rule in contract.get("rules", []):
        failed = _evaluate_expression(frame, rule["expression"])
        if failed.any():
            issues.append(
                ContractIssue(
                    source_system,
                    rule["name"],
                    rule.get("severity", "error"),
                    int(failed.sum()),
                    rule["expression"],
                )
            )
    return issues


def _invalid_type_mask(series: pd.Series, expected_type: str) -> pd.Series:
    if expected_type in {"date", "timestamp"}:
        return pd.to_datetime(series, errors="coerce").isna() & series.notna()
    if expected_type in {"integer", "numeric"}:
        return pd.to_numeric(series, errors="coerce").isna() & series.notna()
    return pd.Series(False, index=series.index)


def _evaluate_expression(frame: pd.DataFrame, expression: str) -> pd.Series:
    try:
        result = frame.eval(expression)
        if result.dtype != bool:
            return pd.Series(False, index=frame.index)
        return ~result.fillna(False)
    except Exception:
        return pd.Series(False, index=frame.index)


def run_contract_checks() -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    contracts = load_contracts()
    rows = []
    for source_system, contract in contracts.get("sources", {}).items():
        files = discover_raw_files(config, source_system)
        source_row_count = 0
        issue_count = 0
        for file_path in files:
            if not file_path.exists():
                rows.append(
                    {
                        "source_system": source_system,
                        "file": str(file_path.relative_to(config.project_root)),
                        "rule_name": "file_available_during_scan",
                        "severity": "warning",
                        "failed_count": 1,
                        "detail": "File disappeared before contract scan could read it, likely due to a concurrent lake refresh.",
                    }
                )
                continue
            frame = read_frame(file_path)
            source_row_count += len(frame)
            issues = validate_frame_against_contract(source_system, frame, contract)
            issue_count += len(issues)
            for issue in issues:
                rows.append(
                    {
                        "source_system": issue.source_system,
                        "file": str(file_path.relative_to(config.project_root)),
                        "rule_name": issue.rule_name,
                        "severity": issue.severity,
                        "failed_count": issue.failed_count,
                        "detail": issue.detail,
                    }
                )
        if not files:
            rows.append(
                {
                    "source_system": source_system,
                    "file": None,
                    "rule_name": "source_files_present",
                    "severity": "error",
                    "failed_count": 1,
                    "detail": "No raw files found for contracted source.",
                }
            )
        elif issue_count == 0:
            rows.append(
                {
                    "source_system": source_system,
                    "file": "all",
                    "rule_name": "contract_passed",
                    "severity": "info",
                    "failed_count": 0,
                    "detail": f"{source_row_count} rows evaluated.",
                }
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_path": str(CONTRACT_PATH.relative_to(config.project_root)),
        "status": "passed" if not any(row["severity"] == "error" for row in rows) else "failed",
        "issue_count": len([row for row in rows if row["severity"] != "info"]),
        "results": rows,
    }
    output_dir = config.quality_report_dir / "contracts"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "contract_check_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(output_dir / "contract_check_results.csv", index=False)
    return report


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Validate raw lake files against source data contracts.").parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_contract_checks(), indent=2))


if __name__ == "__main__":
    main()
