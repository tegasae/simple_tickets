#!/usr/bin/env python3
"""Extract the running OpenAPI and workflow/SQLite facts without using working data."""
import argparse
import importlib.metadata
import json
import os
import platform
import secrets
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

def schema_catalog(connection):
    def rows(query):
        return [dict(row) for row in connection.execute(query)]

    connection.row_factory = sqlite3.Row
    table_names = [row["name"] for row in rows(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    for name in table_names:
        if not name.isidentifier():
            raise ValueError(f"Unanticipated table name {name!r}")
    tables = {}
    for name in table_names:
        indexes = rows(f"PRAGMA index_list({name})")
        for index in indexes:
            if not index["name"].isidentifier():
                raise ValueError(f"Unanticipated index name {index['name']!r}")
            index["columns"] = [row["name"] for row in rows(f"PRAGMA index_info({index['name']})")]
        tables[name] = {
            "columns": rows(f"PRAGMA table_info({name})"),
            "foreign_keys": rows(f"PRAGMA foreign_key_list({name})"),
            "indexes": indexes,
            "ddl": connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
            ).fetchone()[0],
        }
    return tables

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    snapshot = args.snapshot.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(snapshot))
    with tempfile.TemporaryDirectory(prefix="tickets-catalog-") as temporary:
        root = Path(temporary)
        schema = snapshot / "db" / "schema.sql"
        db_path = root / "synthetic.sqlite"
        with closing(sqlite3.connect(db_path)) as connection:
            connection.executescript(schema.read_text(encoding="utf-8"))
            tables = schema_catalog(connection)
        os.chdir(root)
        os.environ["DATABASE_URL"] = str(db_path)
        os.environ["SECRET_KEY"] = secrets.token_hex(32)
        from fastapi.testclient import TestClient
        from src.domain.statuses.mapping_statuses import TICKET_TO_TICKET_USER_STATUS
        from src.domain.statuses.rules.ticket_status_transition import TICKET_TRANSITIONS
        from src.domain.statuses.ticket_user_status_transitions import TICKET_USER_TRANSITIONS
        from src.web.main import create_app
        from utils.db.connect import Connection

        with closing(Connection.create_connection(str(db_path), engine=sqlite3)) as application_db:
            pragmas = {key: application_db.connect.execute(f"PRAGMA {key}").fetchone()[0]
                       for key in ("foreign_keys", "journal_mode", "busy_timeout")}
            assert pragmas["foreign_keys"] == 1
            thread_check = False  # Connection.create_connection default parameter.
        app = create_app()
        assert app.state.settings.DATABASE_URL == str(db_path)
        with TestClient(app) as client:
            health = client.get("/health")
            openapi = client.get("/openapi.json")
            assert health.status_code == openapi.status_code == 200
            definition = openapi.json()
        workflows = {
            "ticket": {before.value: {after.value: [validator.__name__ for validator in rule.validators]
                                       for after, rule in following.items()}
                       for before, following in TICKET_TRANSITIONS.items()},
            "ticket_user": {before.value: sorted(after.value for after in following)
                            for before, following in TICKET_USER_TRANSITIONS.items()},
            "mapping": {internal.value: public.value
                        for internal, public in TICKET_TO_TICKET_USER_STATUS.items()},
        }
        environment = {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "packages": {name: importlib.metadata.version(name) for name in
                         ("fastapi", "pydantic", "pydantic-settings", "PyJWT", "starlette", "uvicorn", "httpx")},
            "health": {"status": health.status_code, "body": health.json()},
            "openapi_status": openapi.status_code,
            "connection": {**pragmas, "check_same_thread": thread_check},
            "json_catalog": [name for name in ("openapi", "tables", "workflows")],
        }
        for name, data in (("openapi", definition), ("tables", tables),
                           ("workflows", workflows), ("environment", environment)):
            (output / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

if __name__ == "__main__":
    main()
