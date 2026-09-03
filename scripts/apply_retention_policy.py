from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_DIR = PROJECT_ROOT / "governance" / "generated"
OUTPUT_DIR = GOVERNANCE_DIR


def _load_retention_policy() -> pd.DataFrame:
    path = GOVERNANCE_DIR / "retention_policy_matrix.csv"
    if not path.exists():
        from scripts.generate_governance_pack import generate_governance_pack

        generate_governance_pack()
    return pd.read_csv(path)


def build_retention_actions(as_of: datetime | None = None) -> pd.DataFrame:
    as_of = as_of or datetime.now(timezone.utc)
    retention = _load_retention_policy()
    rows = []
    for _, row in retention.iterrows():
        retention_days = int(row["retention_days"])
        rows.append(
            {
                "retention_policy": row["retention_policy"],
                "applies_to": row["applies_to"],
                "retention_days": retention_days,
                "disposition_action": row["disposition_action"],
                "cutoff_rule": "retain_until_superseded"
                if retention_days <= 0
                else f"records older than {retention_days} days",
                "as_of_date": as_of.date().isoformat(),
                "planned_sql_pattern": _sql_pattern(str(row["retention_policy"]), retention_days, str(row["disposition_action"])),
                "execution_mode": "dry_run",
            }
        )
    return pd.DataFrame(rows)


def _sql_pattern(policy: str, retention_days: int, disposition_action: str) -> str:
    if retention_days <= 0:
        return "-- retain records until superseded by a new governed definition"
    if disposition_action == "anonymize":
        return f"-- update eligible {policy} records by hashing natural identifiers older than interval '{retention_days} days'"
    if disposition_action == "aggregate_then_delete":
        return f"-- aggregate eligible {policy} records, then delete detail older than interval '{retention_days} days'"
    if disposition_action == "archive_then_delete":
        return f"-- copy eligible {policy} records to archive storage, then delete older than interval '{retention_days} days'"
    if disposition_action == "delete":
        return f"-- delete eligible {policy} records older than interval '{retention_days} days'"
    return f"-- archive eligible {policy} records older than interval '{retention_days} days'"


def generate_retention_dry_run() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    actions = build_retention_actions()
    csv_path = OUTPUT_DIR / "retention_policy_dry_run.csv"
    json_path = OUTPUT_DIR / "retention_policy_dry_run_summary.json"
    actions.to_csv(csv_path, index=False)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "dry_run",
        "policy_count": len(actions),
        "delete_or_anonymize_count": int(actions["disposition_action"].isin(["delete", "anonymize", "aggregate_then_delete"]).sum()),
        "report": str(csv_path.relative_to(PROJECT_ROOT)),
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Generate a dry-run retention enforcement plan.").parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(generate_retention_dry_run(), indent=2))


if __name__ == "__main__":
    main()
