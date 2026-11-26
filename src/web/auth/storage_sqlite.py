import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.web.auth.exceptions import TokenError, TokenNotFoundError
from src.web.auth.storage import TokenStorage
from src.web.auth.tokens import RefreshToken, SubjectType, hash_token


class TokenStorageSQLite(TokenStorage):
    """Store refresh session metadata by hash in a shared SQLite file."""

    def __init__(self, path: Path) -> None:
        if str(path) == ":memory:":
            raise ValueError("Use the memory backend for process-local sessions")
        self.path = path
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS refresh_sessions (
                    token_hash TEXT PRIMARY KEY,
                    subject_id INTEGER NOT NULL,
                    subject_type TEXT NOT NULL,
                    username TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    used INTEGER NOT NULL,
                    revoked INTEGER NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS refresh_sessions_by_identity
                    ON refresh_sessions(username, subject_type, subject_id);
                CREATE INDEX IF NOT EXISTS refresh_sessions_by_expiry
                    ON refresh_sessions(expires_at);
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path)) as db, db:
            yield db

    @staticmethod
    def _insert(db: sqlite3.Connection, token: RefreshToken) -> None:
        expires = token.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        db.execute(
            """INSERT INTO refresh_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (token.token_hash, token.subject_id, token.subject_type, token.username,
             expires.timestamp(), token.used, token.revoked,
             token.model_dump_json(exclude={"token_id"})),
        )

    @staticmethod
    def _decode(row, token_id: str = "") -> RefreshToken:
        token_hash, payload, revoked = row
        token = RefreshToken.model_validate_json(payload)
        return token.model_copy(update={
            "token_id": token_id, "stored_hash": token_hash, "revoked": bool(revoked),
        })

    @staticmethod
    def _find(db: sqlite3.Connection, token_hash: str):
        row = db.execute(
            """SELECT token_hash, payload, revoked
               FROM refresh_sessions WHERE token_hash = ?""",
            (token_hash,),
        ).fetchone()
        if row is None:
            raise TokenNotFoundError()
        return row

    def put(self, refresh_token: RefreshToken) -> None:
        with self._connection() as db:
            self._insert(db, refresh_token)

    def get(self, token_id: str) -> RefreshToken:
        with self._connection() as db:
            return self._decode(self._find(db, hash_token(token_id)), token_id)

    def delete(self, token_id: str) -> None:
        with self._connection() as db:
            removed = db.execute(
                "DELETE FROM refresh_sessions WHERE token_hash = ?", (hash_token(token_id),),
            )
            if removed.rowcount == 0:
                raise TokenNotFoundError()

    def replace(self, token_id: str, successor: RefreshToken) -> None:
        old_hash = hash_token(token_id)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if not self._decode(self._find(db, old_hash), token_id).is_valid():
                raise TokenError("Invalid refresh token")
            self._insert(db, successor)
            db.execute("DELETE FROM refresh_sessions WHERE token_hash = ?", (old_hash,))

    def cleanup_expired_tokens(self) -> int:
        with self._connection() as db:
            return db.execute(
                "DELETE FROM refresh_sessions WHERE expires_at <= ? OR used = 1 OR revoked = 1",
                (datetime.now(timezone.utc).timestamp(),),
            ).rowcount

    def get_user_tokens(self, username: str) -> list[RefreshToken]:
        with self._connection() as db:
            rows = db.execute(
                "SELECT token_hash, payload, revoked FROM refresh_sessions WHERE username = ?",
                (username,),
            )
            return [self._decode(row) for row in rows]

    def revoke_user_tokens(
        self, username: str, *, subject_id: int | None = None,
        subject_type: SubjectType | None = None,
    ) -> int:
        with self._connection() as db:
            return db.execute(
                """UPDATE refresh_sessions SET revoked = 1
                   WHERE username = ? AND (? IS NULL OR subject_id = ?)
                   AND (? IS NULL OR subject_type = ?)""",
                (username, subject_id, subject_id, subject_type, subject_type),
            ).rowcount

    def count(self) -> int:
        with self._connection() as db:
            return db.execute("SELECT COUNT(*) FROM refresh_sessions").fetchone()[0]

    def clear(self) -> None:
        with self._connection() as db:
            db.execute("DELETE FROM refresh_sessions")
