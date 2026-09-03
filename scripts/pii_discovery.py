from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "governance" / "generated"

PATTERNS = {
    "direct_identifier": re.compile(r"(customer_id|lead_id|visitor_id|session_id|rep_id|email|phone|name)", re.IGNORECASE),
    "attribution_identifier": re.compile(r"(attribution_id|utm_|campaign_id)", re.IGNORECASE),
    "commercially_sensitive": re.compile(r"(deal_value|gross_margin|revenue|margin|budget|spend)", re.IGNORECASE),
    "location": re.compile(r"(country|region|territory|geo|location)", re.IGNORECASE),
}

SEARCH_ROOTS = [
    PROJECT_ROOT / "dbt" / "models",
    PROJECT_ROOT / "warehouse" / "postgres",
    PROJECT_ROOT / "semantic_layer",
    PROJECT_ROOT / "governance" / "generated",
]


def classify_field(field_name: str) -> tuple[str, str]:
    for classification, pattern in PATTERNS.items():
        if pattern.search(field_name):
            return classification, pattern.pattern
    return "not_sensitive", ""


def discover_fields(search_roots: list[Path] | None = None) -> pd.DataFrame:
    roots = search_roots or SEARCH_ROOTS
    rows = []
    seen: set[tuple[str, str]] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".sql", ".yml", ".yaml", ".md", ".csv", ".tmdl"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text))):
                classification, matched_pattern = classify_field(token)
                if classification == "not_sensitive":
                    continue
                try:
                    relative_file = str(path.relative_to(PROJECT_ROOT))
                except ValueError:
                    relative_file = str(path)
                key = (relative_file, token)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "file_path": key[0],
                        "field_name": token,
                        "pii_classification": classification,
                        "matched_pattern": matched_pattern,
                        "review_status": "needs_review"
                        if classification in {"direct_identifier", "commercially_sensitive"}
                        else "monitor",
                    }
                )
    columns = ["file_path", "field_name", "pii_classification", "matched_pattern", "review_status"]
    return pd.DataFrame(rows, columns=columns).sort_values(["pii_classification", "file_path", "field_name"])


def generate_pii_discovery_report() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = discover_fields()
    csv_path = OUTPUT_DIR / "pii_discovery_report.csv"
    json_path = OUTPUT_DIR / "pii_discovery_summary.json"
    results.to_csv(csv_path, index=False)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sensitive_field_mentions": len(results),
        "classification_counts": results["pii_classification"].value_counts().to_dict() if not results.empty else {},
        "needs_review_count": int(results["review_status"].eq("needs_review").sum()) if not results.empty else 0,
        "report": str(csv_path.relative_to(PROJECT_ROOT)),
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Scan project schemas/docs for likely PII or sensitive BI fields.").parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(generate_pii_discovery_report(), indent=2))


if __name__ == "__main__":
    main()
