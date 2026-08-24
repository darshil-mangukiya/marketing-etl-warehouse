from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ExtractionWindow:
    start_date: date
    end_date: date
    watermark: str | None = None

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("Extraction end_date cannot precede start_date.")


@dataclass(frozen=True)
class PageResult:
    records: list[dict]
    next_page_token: str | None = None
    request_id: str | None = None
    rate_limit_remaining: int | None = None


@dataclass
class ExtractionResult:
    source_system: str
    records: list[dict] = field(default_factory=list)
    page_count: int = 0
    retry_count: int = 0
    last_watermark: str | None = None
    response_metadata: list[dict] = field(default_factory=list)
