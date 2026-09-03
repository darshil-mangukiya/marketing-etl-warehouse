from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _request_once(base_url: str, token: str, source: str, page_size: int) -> dict:
    started = time.perf_counter()
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/v1/{source}/records",
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": page_size},
            timeout=15,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "success": response.ok,
            "record_count": response.json().get("record_count", 0) if response.ok else 0,
        }
    except Exception as exc:
        return {
            "status_code": None,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "success": False,
            "record_count": 0,
            "error": str(exc),
        }


def run_api_load_test(
    base_url: str = "http://localhost:8000",
    token: str = "local-dev-token",
    source: str = "google_ads",
    requests_count: int = 20,
    concurrency: int = 4,
    page_size: int = 500,
) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(_request_once, base_url, token, source, page_size)
            for _ in range(requests_count)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    latencies = [result["elapsed_ms"] for result in results]
    success_count = sum(1 for result in results if result["success"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_at,
        "base_url": base_url,
        "source": source,
        "requests": requests_count,
        "concurrency": concurrency,
        "success_count": success_count,
        "failure_count": requests_count - success_count,
        "records_returned": sum(result["record_count"] for result in results),
        "latency_ms": {
            "min": min(latencies) if latencies else None,
            "mean": statistics.mean(latencies) if latencies else None,
            "p95": sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "results": results,
    }
    output_dir = PROJECT_ROOT / "benchmarks" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "api_load_test_latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight load test against the mock marketing API.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", default="local-dev-token")
    parser.add_argument("--source", default="google_ads")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--page-size", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            run_api_load_test(
                base_url=args.base_url,
                token=args.token,
                source=args.source,
                requests_count=args.requests,
                concurrency=args.concurrency,
                page_size=args.page_size,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
