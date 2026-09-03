from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KPI_CATALOG_PATH = PROJECT_ROOT / "semantic" / "kpi_catalog.yml"


def load_kpi_catalog() -> dict[str, Any]:
    if not KPI_CATALOG_PATH.exists():
        return {"kpis": {}}
    return yaml.safe_load(KPI_CATALOG_PATH.read_text(encoding="utf-8")) or {"kpis": {}}


def kpi_formula(kpi_key: str) -> str:
    catalog = load_kpi_catalog()
    return str(catalog.get("kpis", {}).get(kpi_key, {}).get("formula", ""))
