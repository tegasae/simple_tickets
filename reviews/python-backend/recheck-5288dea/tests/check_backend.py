"""Syntax, gateway preparation and real app smoke in a disposable source copy.

Run from the root of a source-only temporary copy, never a working checkout.
This is a command-line check, not part of the 104 pytest cases.
"""
import ast
import importlib
import inspect
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import tempfile


def main():
    root = Path.cwd()
    if (root / ".git").exists() or (root / ".env").exists():
        raise SystemExit("Use an isolated source copy without .git or .env")
    files = sorted((root / "src").rglob("*.py"))
    files += sorted((root / "utils").rglob("*.py"))
    files += [root / name for name in ("main.py", "models.py", "config.py")]
    for path in files:
        ast.parse(path.read_text(), filename=str(path.relative_to(root)))
    results = {"ast_files": len(files), "ast": "passed"}
    with tempfile.TemporaryDirectory(prefix="tickets-smoke-") as directory:
        path = Path(directory) / "synthetic.sqlite3"
        with sqlite3.connect(path) as database:
            database.executescript((root / "db/schema.sql").read_text())
            database.execute("PRAGMA foreign_keys=ON")
            count = 0
            for file in sorted((root / "src/adapters/repositories/gateways").glob("*.py")):
                module = importlib.import_module(
                    "src.adapters.repositories.gateways." + file.stem
                )
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if cls.__module__ != module.__name__:
                        continue
                    for sql in vars(cls).values():
                        if not isinstance(sql, str):
                            continue
                        words = sql.strip().split()
                        if not words or words[0].upper() not in {
                            "SELECT", "INSERT", "UPDATE", "DELETE"
                        }:
                            continue
                        parameters = {name: 0 for name in re.findall(r":(\w+)", sql)}
                        database.execute("EXPLAIN " + sql, parameters).fetchall()
                        count += 1
            results["sql_prepared"] = count
            results["integrity_check"] = database.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]
            results["foreign_key_violations"] = len(database.execute(
                "PRAGMA foreign_key_check"
            ).fetchall())
            assert results["integrity_check"] == "ok"
            assert results["foreign_key_violations"] == 0

        os.environ["SECRET_KEY"] = secrets.token_hex(32)
        os.environ["DATABASE_URL"] = str(path)
        os.environ["REFRESH_TOKEN_BACKEND"] = "memory"
        modules = ("main", "src.web.main", "src.oauth2.main")
        for name in modules:
            importlib.import_module(name)
        results["imports"] = list(modules)
        from fastapi.testclient import TestClient
        from src.web.main import create_app

        with TestClient(create_app(), raise_server_exceptions=False) as api:
            health = api.get("/health")
            spec = api.get("/openapi.json")
            assert health.status_code == spec.status_code == 200
            assert health.json() == {"status": "ok"}
            results["health_status"] = health.status_code
            results["openapi_status"] = spec.status_code
            results["openapi_paths"] = len(spec.json()["paths"])
    results["command"] = [sys.executable, str(Path(__file__).resolve())]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
