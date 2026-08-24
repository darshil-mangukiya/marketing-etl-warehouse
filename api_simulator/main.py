from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.file_io import read_frame
from api_simulator.pagination import parse_page_token

API_SOURCES = {"google_ads", "facebook_ads", "tiktok_ads"}
DEFAULT_TOKEN = "local-dev-token"


class ApiRecordPage(BaseModel):
    source_system: str
    page_size: int
    record_count: int
    next_page_token: str | None
    watermark_column: str
    generated_at: str
    records: list[dict]


def authenticate(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("MOCK_API_TOKEN", DEFAULT_TOKEN)
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


def manifest_path() -> Path:
    return Path(os.getenv("SOURCE_MANIFEST_PATH", PROJECT_ROOT / "data_sources" / "generated" / "manifest.json"))


def generated_parts(source_system: str) -> list[Path]:
    path = manifest_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Manifest not found at {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    parts = [
        PROJECT_ROOT / part["path"]
        for part in manifest.get("parts", [])
        if part.get("source_system") == source_system
    ]
    if not parts:
        raise HTTPException(status_code=404, detail=f"No generated parts found for {source_system}")
    return parts


def maybe_fail(response: Response, failure_rate: float) -> None:
    response.headers["x-api-rate-limit-remaining"] = str(random.randint(100, 5000))
    response.headers["x-api-request-id"] = f"mock-{random.randint(100000, 999999)}"
    if random.random() < failure_rate:
        raise HTTPException(status_code=503, detail="Simulated upstream API failure")


def records_page(
    source_system: str,
    page_size: int,
    page_token: str | None,
    updated_after: str | None,
) -> ApiRecordPage:
    parts = generated_parts(source_system)
    file_index, row_offset = parse_page_token(page_token)
    records: list[dict] = []
    next_token: str | None = None
    updated_after_ts = pd.Timestamp(updated_after) if updated_after else None

    for current_file_index in range(file_index, len(parts)):
        frame = read_frame(parts[current_file_index])
        if updated_after_ts is not None and "updated_at" in frame.columns:
            frame = frame.loc[pd.to_datetime(frame["updated_at"], errors="coerce") > updated_after_ts]
        if current_file_index == file_index and row_offset:
            frame = frame.iloc[row_offset:]
        if frame.empty:
            row_offset = 0
            continue
        needed = page_size - len(records)
        page = frame.head(needed)
        records.extend(_json_ready(page).to_dict(orient="records"))
        if len(frame) > needed:
            consumed_offset = (row_offset if current_file_index == file_index else 0) + needed
            next_token = f"{current_file_index}:{consumed_offset}"
            break
        row_offset = 0
    return ApiRecordPage(
        source_system=source_system,
        page_size=page_size,
        record_count=len(records),
        next_page_token=next_token,
        watermark_column="updated_at",
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=records,
    )


def _json_ready(frame: pd.DataFrame) -> pd.DataFrame:
    converted = frame.copy()
    for column in converted.columns:
        if pd.api.types.is_datetime64_any_dtype(converted[column]):
            converted[column] = converted[column].astype(str)
    return converted.where(pd.notna(converted), None)


app = FastAPI(
    title="Marketing Platform Mock Source APIs",
    version="1.0.0",
    description=(
        "Paginated, bearer-token protected mock APIs for Google Ads, Facebook Ads, and TikTok Ads. "
        "Backed by the synthetic generated source partitions."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "manifest_exists": manifest_path().exists(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/sources")
def sources(_: Annotated[None, Depends(authenticate)]) -> dict:
    return {
        "sources": sorted(API_SOURCES),
        "pagination": "page_token",
        "watermark_column": "updated_at",
    }


@app.get("/v1/{source_system}/records", response_model=ApiRecordPage)
def source_records(
    source_system: str,
    response: Response,
    _: Annotated[None, Depends(authenticate)],
    page_size: int = Query(500, ge=1, le=5000),
    page_token: str | None = Query(None),
    updated_after: str | None = Query(None),
    failure_rate: float = Query(0.0, ge=0.0, le=0.5),
) -> ApiRecordPage:
    if source_system not in API_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unsupported source system: {source_system}")
    maybe_fail(response, failure_rate)
    return records_page(
        source_system=source_system,
        page_size=page_size,
        page_token=page_token,
        updated_after=updated_after,
    )
