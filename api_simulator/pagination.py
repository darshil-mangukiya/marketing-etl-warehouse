from __future__ import annotations

from fastapi import HTTPException


def parse_page_token(token: str | None) -> tuple[int, int]:
    if not token:
        return 0, 0
    try:
        file_index, row_offset = token.split(":", 1)
        return max(int(file_index), 0), max(int(row_offset), 0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid page token") from exc
