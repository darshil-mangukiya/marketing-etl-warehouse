from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_catalog import generate_catalog

OUTPUT_ROOT = PROJECT_ROOT / "metadata" / "generated"
NAMESPACE = "marketing-etl-platform"


def generate_lineage_metadata() -> dict:
    catalog = generate_catalog()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    openlineage_events = build_openlineage_events(catalog)
    datahub_mces = build_datahub_mces(catalog)
    summary = build_lineage_summary(catalog, openlineage_events, datahub_mces)

    (OUTPUT_ROOT / "openlineage_events.jsonl").write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in openlineage_events) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "datahub_mces.json").write_text(json.dumps(datahub_mces, indent=2), encoding="utf-8")
    (OUTPUT_ROOT / "lineage_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_ROOT / "lineage_summary.md").write_text(render_lineage_summary(catalog, summary), encoding="utf-8")
    return summary


def build_openlineage_events(catalog: dict) -> list[dict]:
    generated_at = datetime.now(timezone.utc).isoformat()
    model_lookup = {model["name"]: model for model in catalog.get("models", [])}
    edges_by_downstream: dict[str, list[dict]] = {}
    for edge in lineage_edges_from_catalog(catalog):
        edges_by_downstream.setdefault(edge["downstream"], []).append(edge)

    events = []
    for downstream, edges in sorted(edges_by_downstream.items()):
        model = model_lookup.get(downstream, {"layer": "unknown"})
        events.append(
            {
                "eventType": "COMPLETE",
                "eventTime": generated_at,
                "producer": "https://openlineage.io",
                "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
                "run": {"runId": f"{downstream}-{generated_at}"},
                "job": {
                    "namespace": NAMESPACE,
                    "name": f"dbt.{model.get('layer', 'unknown')}.{downstream}",
                    "facets": {
                        "documentation": {
                            "_producer": NAMESPACE,
                            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationJobFacet.json",
                            "description": f"dbt model `{downstream}` in the {model.get('layer', 'unknown')} layer.",
                        }
                    },
                },
                "inputs": [
                    {
                        "namespace": NAMESPACE,
                        "name": edge["upstream"],
                        "facets": {"sourceType": {"_producer": NAMESPACE, "_schemaURL": "custom", "type": edge["edge_type"]}},
                    }
                    for edge in edges
                ],
                "outputs": [
                    {
                        "namespace": NAMESPACE,
                        "name": downstream,
                        "facets": {"layer": {"_producer": NAMESPACE, "_schemaURL": "custom", "name": model.get("layer", "unknown")}},
                    }
                ],
            }
        )
    return events


def build_datahub_mces(catalog: dict) -> list[dict]:
    upstreams_by_downstream: dict[str, list[dict]] = {}
    for edge in lineage_edges_from_catalog(catalog):
        upstreams_by_downstream.setdefault(edge["downstream"], []).append(edge)

    events = []
    for model in sorted(catalog.get("models", []), key=lambda item: item["name"]):
        upstreams = upstreams_by_downstream.get(model["name"], [])
        events.append(
            {
                "entityType": "dataset",
                "entityUrn": dataset_urn(model["name"], model.get("layer", "unknown")),
                "changeType": "UPSERT",
                "aspectName": "upstreamLineage",
                "aspect": {
                    "upstreams": [
                        {
                            "dataset": dataset_urn(edge["upstream"], "source" if edge["edge_type"] == "source" else "dbt"),
                            "type": "TRANSFORMED",
                            "auditStamp": {
                                "time": int(datetime.now(timezone.utc).timestamp() * 1000),
                                "actor": "urn:li:corpuser:data_platform",
                            },
                        }
                        for edge in upstreams
                    ]
                },
            }
        )

    for asset in catalog.get("semantic_assets", []):
        events.append(
            {
                "entityType": "dashboard" if asset["asset_type"] == "exposure" else "chart",
                "entityUrn": f"urn:li:{asset['asset_type']}:(powerbi,{asset['name']})",
                "changeType": "UPSERT",
                "aspectName": "ownership",
                "aspect": {
                    "owners": [
                        {
                            "owner": "urn:li:corpuser:analytics_engineering",
                            "type": "DATAOWNER",
                        }
                    ]
                },
            }
        )
    return events


def lineage_edges_from_catalog(catalog: dict) -> list[dict]:
    edges = []
    for model in catalog.get("models", []):
        for ref in model.get("refs", []):
            edges.append({"upstream": ref, "downstream": model["name"], "edge_type": "model_ref"})
        for source in model.get("sources", []):
            edges.append({"upstream": source, "downstream": model["name"], "edge_type": "source"})
    return edges


def build_lineage_summary(catalog: dict, openlineage_events: list[dict], datahub_mces: list[dict]) -> dict:
    reporting_models = [model["name"] for model in catalog.get("models", []) if model.get("layer") == "reporting"]
    warehouse_models = [model["name"] for model in catalog.get("models", []) if model.get("layer") == "warehouse"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "openlineage_event_count": len(openlineage_events),
        "datahub_mce_count": len(datahub_mces),
        "source_count": len(catalog.get("sources", [])),
        "warehouse_model_count": len(warehouse_models),
        "reporting_model_count": len(reporting_models),
        "critical_marts": catalog.get("critical_marts", []),
        "outputs": {
            "openlineage_events": "metadata/generated/openlineage_events.jsonl",
            "datahub_mces": "metadata/generated/datahub_mces.json",
            "summary": "metadata/generated/lineage_summary.md",
        },
    }


def render_lineage_summary(catalog: dict, summary: dict) -> str:
    critical = "\n".join(f"- `{mart}`" for mart in summary["critical_marts"])
    return (
        "# Lineage Metadata Export\n\n"
        "This export translates the local dbt/catalog graph into OpenLineage-style run events and "
        "DataHub-style metadata change events. It is intentionally dependency-free so it can be generated "
        "during local demos without a running metadata platform.\n\n"
        f"- OpenLineage events: `{summary['openlineage_event_count']}`\n"
        f"- DataHub metadata events: `{summary['datahub_mce_count']}`\n"
        f"- Sources: `{summary['source_count']}`\n"
        f"- Warehouse models: `{summary['warehouse_model_count']}`\n"
        f"- Reporting models: `{summary['reporting_model_count']}`\n\n"
        "Critical marts represented in lineage:\n"
        f"{critical}\n\n"
        "Primary metadata files:\n"
        "- `openlineage_events.jsonl`\n"
        "- `datahub_mces.json`\n"
        "- `lineage_manifest.json`\n"
    )


def dataset_urn(name: str, layer: str) -> str:
    platform = "postgres" if layer not in {"source", "dbt"} else layer
    dataset_name = name.replace(".", "_")
    return f"urn:li:dataset:(urn:li:dataPlatform:{platform},marketing_warehouse.{layer}.{dataset_name},PROD)"


def main() -> None:
    print(json.dumps(generate_lineage_metadata(), indent=2))


if __name__ == "__main__":
    main()
