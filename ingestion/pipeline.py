from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.generators import DEFAULT_CONFIG, run_generation
from ingestion.config import PlatformConfig
from ingestion.extractors import IngestionManager


def run_pipeline(profile: str = "dev", generate: bool = False, clean_generation: bool = True) -> dict:
    config = PlatformConfig.from_env()
    config.ensure_dirs()
    if generate:
        run_generation(profile=profile, config_path=DEFAULT_CONFIG, clean=clean_generation)
    manager = IngestionManager(config=config)
    return manager.ingest_manifest(config.source_manifest_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run marketing ingestion pipeline.")
    parser.add_argument("--profile", default="dev", help="Data generation profile to use when --generate is set.")
    parser.add_argument("--generate", action="store_true", help="Generate source data before ingestion.")
    parser.add_argument("--no-clean", action="store_true", help="Do not clean generated source output first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_pipeline(profile=args.profile, generate=args.generate, clean_generation=not args.no_clean)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
