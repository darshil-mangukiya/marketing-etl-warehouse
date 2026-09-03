from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def read_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".json", ".jsonl"}:
        return pd.read_json(path, lines=True)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported file type for {path}")


def write_frame(frame: pd.DataFrame, path: Path, preferred_format: str | None = None) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = (preferred_format or path.suffix.lstrip(".") or "csv").lower()
    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401

            path = path.with_suffix(".parquet")
            frame.to_parquet(path, index=False)
            return path, "parquet"
        except Exception:
            fmt = "csv"
    if fmt in {"json", "jsonl"}:
        path = path.with_suffix(".jsonl")
        frame.to_json(path, orient="records", lines=True, date_format="iso")
        return path, "jsonl"
    path = path.with_suffix(".csv")
    frame.to_csv(path, index=False)
    return path, "csv"


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, default=str) + "\n")
