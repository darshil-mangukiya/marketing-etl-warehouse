from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ingestion.file_io import read_frame


@dataclass(frozen=True)
class ApiPage:
    source_system: str
    page_number: int
    records: list[dict]
    next_page_token: str | None


class FileBackedRestClient:
    """Paginated REST API simulator backed by generated source files."""

    def __init__(self, source_system: str, file_paths: list[Path], page_size: int = 1000) -> None:
        self.source_system = source_system
        self.file_paths = file_paths
        self.page_size = page_size

    def pages(self) -> Iterator[ApiPage]:
        page_number = 0
        for file_path in self.file_paths:
            frame = read_frame(file_path)
            for start in range(0, len(frame), self.page_size):
                page = frame.iloc[start : start + self.page_size]
                page_number += 1
                next_token = f"{file_path.name}:{start + self.page_size}" if start + self.page_size < len(frame) else None
                yield ApiPage(
                    source_system=self.source_system,
                    page_number=page_number,
                    records=page.to_dict(orient="records"),
                    next_page_token=next_token,
                )


def api_sources() -> set[str]:
    return {"google_ads", "facebook_ads", "tiktok_ads"}
