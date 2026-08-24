from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_ROOT = PROJECT_ROOT / "dbt"
CATALOG_DIR = PROJECT_ROOT / "catalog" / "generated"


def generate_catalog() -> dict:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((PROJECT_ROOT / "catalog" / "catalog_config.yml").read_text(encoding="utf-8"))
    models = _dbt_models()
    sources = _dbt_sources()
    semantic = _semantic_assets()
    lineage_edges = _lineage_edges(models)
    field_dictionary = _field_dictionary(models)

    catalog = {
        "catalog_name": config["catalog_name"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "models": len(models),
            "sources": len(sources),
            "semantic_assets": len(semantic),
            "lineage_edges": len(lineage_edges),
            "fields": len(field_dictionary),
        },
        "sources": sources,
        "models": models,
        "semantic_assets": semantic,
        "critical_marts": config["critical_marts"],
    }
    (CATALOG_DIR / "data_catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    pd.DataFrame(lineage_edges).to_csv(CATALOG_DIR / "lineage_edges.csv", index=False)
    pd.DataFrame(field_dictionary).to_csv(CATALOG_DIR / "bi_field_dictionary.csv", index=False)
    (CATALOG_DIR / "lineage_diagram.md").write_text(_lineage_mermaid(lineage_edges), encoding="utf-8")
    return catalog


def _dbt_models() -> list[dict]:
    models = []
    for sql_path in sorted((DBT_ROOT / "models").rglob("*.sql")):
        relative = sql_path.relative_to(DBT_ROOT)
        layer = _layer_for_path(relative)
        sql = sql_path.read_text(encoding="utf-8")
        models.append(
            {
                "name": sql_path.stem,
                "layer": layer,
                "path": str(relative),
                "refs": sorted(set(re.findall(r"ref\(['\"]([^'\"]+)['\"]\)", sql))),
                "sources": sorted(
                    set(
                        f"{source}.{table}"
                        for source, table in re.findall(
                            r"source\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)",
                            sql,
                        )
                    )
                ),
            }
        )
    return models


def _dbt_sources() -> list[dict]:
    sources_yml = yaml.safe_load((DBT_ROOT / "models" / "sources.yml").read_text(encoding="utf-8"))
    sources = []
    for source in sources_yml.get("sources", []):
        for table in source.get("tables", []):
            sources.append(
                {
                    "source": source["name"],
                    "table": table["name"],
                    "schema": source.get("schema"),
                    "description": table.get("description", ""),
                }
            )
    return sources


def _semantic_assets() -> list[dict]:
    semantic_path = DBT_ROOT / "models" / "marts" / "semantic_layer.yml"
    if not semantic_path.exists():
        return []
    payload = yaml.safe_load(semantic_path.read_text(encoding="utf-8"))
    assets = []
    for key in ("semantic_models", "metrics", "exposures"):
        for item in payload.get(key, []):
            assets.append(
                {
                    "asset_type": key.rstrip("s"),
                    "name": item["name"],
                    "description": item.get("description", ""),
                }
            )
    return assets


def _lineage_edges(models: list[dict]) -> list[dict]:
    edges = []
    for model in models:
        for ref in model["refs"]:
            edges.append({"upstream": ref, "downstream": model["name"], "edge_type": "model_ref"})
        for source in model["sources"]:
            edges.append({"upstream": source, "downstream": model["name"], "edge_type": "source"})
    return edges


def _field_dictionary(models: list[dict]) -> list[dict]:
    rows = []
    for model in models:
        if model["layer"] not in {"warehouse", "reporting"}:
            continue
        sql_path = DBT_ROOT / model["path"]
        fields = _extract_select_aliases(sql_path.read_text(encoding="utf-8"))
        for field in fields:
            rows.append(
                {
                    "model": model["name"],
                    "layer": model["layer"],
                    "field_name": field,
                    "business_definition": _business_definition(field),
                    "recommended_visibility": "show" if not field.endswith("_key") else "hide",
                }
            )
    return rows


def _extract_select_aliases(sql: str) -> list[str]:
    aliases = set(re.findall(r"\bas\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, flags=re.IGNORECASE))
    explicit = set(re.findall(r"select\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, flags=re.IGNORECASE))
    return sorted((aliases | explicit) - {"select", "from"})


def _business_definition(field: str) -> str:
    dictionary = {
        "spend": "Paid media spend from source platforms.",
        "booked_revenue": "Sales conversion revenue booked in the sales system.",
        "gross_margin": "Gross margin from closed-won conversions.",
        "roas": "Booked revenue divided by spend.",
        "cac": "Spend divided by closed-won conversions.",
        "lead_to_mql_rate": "Marketing-qualified leads divided by total leads.",
        "revenue_attainment": "Actual revenue divided by target revenue.",
        "monitoring_status": "Operational status derived from freshness, load, and quality signals.",
    }
    return dictionary.get(field, f"Field `{field}` from the modeled analytics layer.")


def _layer_for_path(relative: Path) -> str:
    text = str(relative)
    if "/staging/" in f"/{text}":
        return "staging"
    if "/intermediate/" in f"/{text}":
        return "intermediate"
    if "/marts/core/" in f"/{text}":
        return "warehouse"
    if "/marts/reporting/" in f"/{text}":
        return "reporting"
    return "other"


def _lineage_mermaid(edges: list[dict]) -> str:
    lines = ["# Generated Lineage Diagram", "", "```mermaid", "flowchart LR"]
    for edge in edges[:220]:
        upstream = _node(edge["upstream"])
        downstream = _node(edge["downstream"])
        lines.append(f'    {upstream}["{edge["upstream"]}"] --> {downstream}["{edge["downstream"]}"]')
    lines.append("```")
    return "\n".join(lines) + "\n"


def _node(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value)


def main() -> None:
    print(json.dumps(generate_catalog(), indent=2))


if __name__ == "__main__":
    main()
