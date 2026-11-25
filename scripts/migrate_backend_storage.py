"""Upgrade an existing SQLite database using db/schema.sql as the reference.

Run during a deployment window with application writers stopped.
"""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3

VERSION_TABLES = ("departments", "employees", "clients")
STORAGE_TABLES = ("auth_refresh_sessions", "creation_results")
SCHEMA = Path(__file__).resolve().parents[1] / "db" / "schema.sql"

# The previously published dump contains this empty, pre-activation table.
LEGACY_CREATION_RESULTS = """CREATE TABLE creation_results (
    subject_type TEXT NOT NULL CHECK (subject_type IN ('admin', 'user')),
    subject_id INTEGER NOT NULL,
    command TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    status_code INTEGER,
    body TEXT,
    expires_at DOUBLE PRECISION,
    PRIMARY KEY (subject_type, subject_id, command, idempotency_key),
    CHECK ((status_code IS NULL AND body IS NULL AND expires_at IS NULL)
        OR (status_code IS NOT NULL AND status_code BETWEEN 200 AND 299 AND body IS NOT NULL))
)"""


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _ddl(db: sqlite3.Connection, name: str) -> str:
    row = db.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = ?", (name,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Missing expected table {name}")
    return row[0]


def _columns(db: sqlite3.Connection, table: str) -> dict[str, tuple]:
    return {row[1]: row for row in db.execute(f"PRAGMA table_xinfo({_quote(table)})")}


def _fix_version(
    db: sqlite3.Connection, reference: sqlite3.Connection, table: str,
) -> int:
    original = _columns(db, table)
    canonical = _columns(reference, table)
    if original.keys() != canonical.keys():
        raise ValueError(f"Unexpected columns in {table}. Inspect its schema before upgrading.")
    version = original["version"]
    if version[3]:
        if version[4] != "0":
            raise ValueError(f"Unexpected version default in {table}")
        return 0

    declaration = f"CREATE TABLE {table} "
    existing = _ddl(db, table)
    # Accept only the supported old DDL. Preserve unknown schema by refusing
    # an unreviewed rewrite, even when column names match.
    expected = _ddl(reference, table)
    prior = expected.replace("version INTEGER NOT NULL DEFAULT 0", "version INTEGER DEFAULT 0")
    if existing != prior or not expected.startswith(declaration):
        raise ValueError(f"Unexpected DDL for {table}. Review the upgrade first.")

    auxiliary = db.execute(
        """SELECT sql FROM sqlite_schema
           WHERE tbl_name = ? AND type IN ('index', 'trigger') AND sql IS NOT NULL
           ORDER BY type, name""",
        (table,),
    ).fetchall()
    sequence = db.execute("SELECT seq FROM sqlite_sequence WHERE name = ?", (table,)).fetchone()
    old_sql = _quote(table)
    new_name = f"__version_upgrade_{table}"
    new_sql = _quote(new_name)
    target_columns = ", ".join(_quote(name) for name in original)
    projection = ", ".join(
        'COALESCE("version", 0)' if name == "version" else _quote(name) for name in original
    )
    changed = db.execute(f"SELECT COUNT(*) FROM {old_sql} WHERE version IS NULL").fetchone()[0]
    db.execute(expected.replace(declaration, f"CREATE TABLE {new_sql} ", 1))
    db.execute(f"INSERT INTO {new_sql} ({target_columns}) SELECT {projection} FROM {old_sql}")
    db.execute(f"DROP TABLE {old_sql}")
    db.execute(f"ALTER TABLE {new_sql} RENAME TO {old_sql}")
    for (statement,) in auxiliary:
        db.execute(statement)
    if sequence:
        db.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        db.execute("INSERT INTO sqlite_sequence(name, seq) VALUES (?, ?)", (table, sequence[0]))
    return changed


def migrate(db: sqlite3.Connection, *, schema: Path = SCHEMA) -> dict[str, int]:
    """Apply the schema change atomically. Report normalized rows per table."""
    if db.in_transaction:
        raise ValueError("The migration requires its own transaction")
    was_enabled = db.execute("PRAGMA foreign_keys").fetchone()[0]
    with closing(sqlite3.connect(":memory:")) as reference:
        reference.executescript(schema.read_text(encoding="utf-8"))
        db.execute("PRAGMA foreign_keys=OFF")
        try:
            with db:
                db.execute("BEGIN IMMEDIATE")
                changed = {table: _fix_version(db, reference, table) for table in VERSION_TABLES}
                for table in STORAGE_TABLES:
                    present = db.execute(
                        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?", (table,),
                    ).fetchone()
                    expected = _ddl(reference, table)
                    if present and (existing := _ddl(db, table)) != expected:
                        if table != "creation_results" or existing != LEGACY_CREATION_RESULTS:
                            raise ValueError(f"Unexpected DDL for {table}")
                        if db.execute("SELECT 1 FROM creation_results LIMIT 1").fetchone() is not None:
                            raise ValueError("Cannot upgrade a populated legacy creation_results table")
                        db.execute("DROP TABLE creation_results")
                        present = None
                    if not present:
                        db.execute(expected)
                    indexes = reference.execute(
                        "SELECT sql FROM sqlite_schema WHERE tbl_name = ? AND type = 'index' AND sql IS NOT NULL",
                        (table,),
                    )
                    for (statement,) in indexes:
                        db.execute(statement.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ", 1))
                if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise ValueError("Foreign key validation failed. The migration was rolled back.")
        finally:
            db.execute(f"PRAGMA foreign_keys={int(was_enabled)}")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="Path to the existing main SQLite file")
    args = parser.parse_args()
    uri = args.database.resolve(strict=True).as_uri() + "?mode=rw"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        counts = migrate(db)
    for table, count in counts.items():
        print(f"{table}: {count} NULL versions normalized")


if __name__ == "__main__":
    main()
