from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ingestion.config import postgres_url


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or postgres_url(), pool_pre_ping=True)


def execute_sql(engine: Engine, sql: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(sql))
