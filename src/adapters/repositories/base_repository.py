from dataclasses import dataclass
from typing import Any

from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError

from src.adapters.repositories.exceptions import PersistenceError


@dataclass(frozen=True)
class ExecResult:
    last_row_id: int
    rowcount: int


class BaseRepository:
    """
    Base repository helpers for your Connection/Query API.

    Key detail:
    - Query.set_result() sets Query.count (cursor.rowcount) and last_row_id.
    - We return both so callers can implement optimistic locking reliably.
    """

    def __init__(self, conn: Connection):
        self.conn = conn

    def _get_one(self, sql: str, var: list[str] | None = None, params: dict[str, Any] | None = None) -> dict:
        try:
            with self.conn.create_query(sql, var=var) as q:
                return q.get_one_result(params)
        except DBOperationError as e:
            raise PersistenceError(str(e)) from e
        except Exception as e:
            raise PersistenceError(str(e)) from e

    def _get_many(self, sql: str, var: list[str] | None = None, params: dict[str, Any] | None = None) -> list[dict]:
        try:
            with self.conn.create_query(sql, var=var) as q:
                return q.get_result(params)
        except DBOperationError as e:
            raise PersistenceError(str(e)) from e
        except Exception as e:
            raise PersistenceError(str(e)) from e

    def _exec(self, sql: str, params: dict[str, Any] | None = None) -> ExecResult:
        """
        Execute statement and return (last_row_id, rowcount).
        """
        try:
            with self.conn.create_query(sql) as q:
                last_row_id = q.set_result(params)
                return ExecResult(last_row_id=int(last_row_id or 0), rowcount=int(q.count or 0))
        except DBOperationError as e:
            raise PersistenceError(str(e)) from e
        except Exception as e:
            raise PersistenceError(str(e)) from e

    def _exists(self, sql: str, params: dict[str, Any] | None = None) -> bool:
        row = self._get_one(sql, var=["one"], params=params)

        return bool(row.get("one",0))