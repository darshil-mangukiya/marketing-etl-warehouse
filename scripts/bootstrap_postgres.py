from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _admin_connection_kwargs(database: str) -> dict:
    return {
        "host": os.getenv("POSTGRES_ADMIN_HOST", os.getenv("POSTGRES_HOST", "localhost")),
        "port": int(os.getenv("POSTGRES_ADMIN_PORT", os.getenv("POSTGRES_PORT", "5432"))),
        "dbname": database,
        "user": os.getenv("POSTGRES_ADMIN_USER", "postgres"),
        "password": os.getenv("POSTGRES_ADMIN_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
        "connect_timeout": int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "10")),
    }


def bootstrap_postgres(apply_init_sql: bool = True) -> dict:
    try:
        import psycopg2
        from psycopg2 import sql
    except Exception as exc:
        raise RuntimeError("psycopg2 is required for PostgreSQL bootstrap. Install requirements.txt first.") from exc

    target_db = os.getenv("POSTGRES_DB", "marketing_warehouse")
    target_user = os.getenv("POSTGRES_USER", "marketing")
    target_password = os.getenv("POSTGRES_PASSWORD", "marketing")
    admin_db = os.getenv("POSTGRES_ADMIN_DB", "postgres")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_database": target_db,
        "target_user": target_user,
        "role_created": False,
        "database_created": False,
        "init_sql_applied": [],
    }

    connection = psycopg2.connect(**_admin_connection_kwargs(admin_db))
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute("select 1 from pg_roles where rolname = %s", (target_user,))
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("create role {} login password %s").format(sql.Identifier(target_user)),
                (target_password,),
            )
            summary["role_created"] = True
        cursor.execute("select 1 from pg_database where datname = %s", (target_db,))
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("create database {} owner {}").format(
                    sql.Identifier(target_db),
                    sql.Identifier(target_user),
                )
            )
            summary["database_created"] = True
    connection.close()

    if apply_init_sql:
        target_connection = psycopg2.connect(**_admin_connection_kwargs(target_db))
        target_connection.autocommit = True
        init_files = sorted((PROJECT_ROOT / "warehouse" / "postgres" / "init").glob("*.sql"))
        init_files += sorted((PROJECT_ROOT / "warehouse" / "postgres" / "views").glob("*.sql"))
        with target_connection.cursor() as cursor:
            for file_path in init_files:
                cursor.execute(file_path.read_text(encoding="utf-8"))
                summary["init_sql_applied"].append(str(file_path.relative_to(PROJECT_ROOT)))
            _grant_application_permissions(cursor, target_user)
        target_connection.close()

    output_path = PROJECT_ROOT / "data" / "logs" / "postgres_bootstrap_latest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _grant_application_permissions(cursor, target_user: str) -> None:
    from psycopg2 import sql

    schemas = ["raw", "staging", "intermediate", "warehouse", "mart", "semantic", "ops"]
    for schema in schemas:
        cursor.execute(
            sql.SQL("alter schema {} owner to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )
        cursor.execute(
            sql.SQL("grant usage, create on schema {} to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )
        cursor.execute(
            sql.SQL("grant all privileges on all tables in schema {} to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )
        cursor.execute(
            sql.SQL("grant all privileges on all sequences in schema {} to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )
        cursor.execute(
            sql.SQL("alter default privileges in schema {} grant all privileges on tables to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )
        cursor.execute(
            sql.SQL("alter default privileges in schema {} grant all privileges on sequences to {}").format(
                sql.Identifier(schema),
                sql.Identifier(target_user),
            )
        )

    cursor.execute(
        """
        select n.nspname, c.relname, c.relkind
        from pg_class c
        join pg_namespace n
            on c.relnamespace = n.oid
        where n.nspname = any(%s)
          and c.relkind in ('r', 'p', 'v', 'm')
        """,
        (schemas,),
    )
    relation_rows = cursor.fetchall()
    command_by_kind = {
        "r": "alter table",
        "p": "alter table",
        "v": "alter view",
        "m": "alter materialized view",
    }
    for schema, relation, relkind in relation_rows:
        cursor.execute(
            sql.SQL("{} {}.{} owner to {}").format(
                sql.SQL(command_by_kind[relkind]),
                sql.Identifier(schema),
                sql.Identifier(relation),
                sql.Identifier(target_user),
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap local PostgreSQL role, database, schemas, and views.")
    parser.add_argument("--skip-init-sql", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(bootstrap_postgres(apply_init_sql=not args.skip_init_sql), indent=2))


if __name__ == "__main__":
    main()
