from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
import shutil
import sqlite3
from pathlib import Path

import pytest

import src.adapters.repositories.gateways as gateways_pkg

pytestmark = pytest.mark.contract
def _find_source_db() -> Path:
    candidates = [
        Path.cwd() / "db" / "admins.db",
        Path(__file__).resolve().parents[3] / "db" / "admins.db",
        Path(__file__).resolve().parents[2] / "db" / "admins.db",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Cannot find db/admins.db. Run pytest from the project root "
        "or place tests_pyramid inside the project root."
    )


SOURCE_DB = _find_source_db()
PARAM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")


def _sql_constants():
    for module_info in pkgutil.iter_modules(gateways_pkg.__path__):
        module = importlib.import_module(f"{gateways_pkg.__name__}.{module_info.name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            for name, value in vars(cls).items():
                if name.isupper() and isinstance(value, str) and value.strip():
                    yield module_info.name, cls.__name__, name, value


def _bindings(sql: str) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for name in PARAM_RE.findall(sql):
        if name in {"limit", "last_id", "offset"}:
            bindings[name] = 1
        elif "name" in name or "login" in name or "password" in name or "comment" in name or "text" in name:
            bindings[name] = "x"
        elif "date" in name or name.endswith("_at"):
            bindings[name] = "2026-01-01T00:00:00+00:00"
        else:
            bindings[name] = 0
    return bindings


def test_every_gateway_sql_constant_prepares_against_current_database_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "schema.sqlite3"
    shutil.copy2(SOURCE_DB, db_path)
    conn = sqlite3.connect(db_path)
    try:
        failures = []
        count = 0
        for module, cls, name, sql in _sql_constants():
            count += 1
            try:
                conn.execute("EXPLAIN " + sql, _bindings(sql)).fetchall()
            except sqlite3.Error as exc:
                failures.append(f"{module}.{cls}.{name}: {exc}")
        assert count >= 50, "gateway discovery unexpectedly found too few SQL constants"
        assert failures == []
    finally:
        conn.close()
