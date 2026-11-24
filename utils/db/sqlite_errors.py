"""Translate native SQLite failures into driver-neutral operation errors.

A future driver supplies its own translation to the same exception types.
No application service needs to inspect native codes or retry SQL statements.
"""
import sqlite3

from .exceptions import DBOperationError, DBTransientError, DBUniqueConstraintError


def operation_error(error: Exception, *, operation: str = "") -> DBOperationError:
    context = f"{operation}: " if operation else ""
    if isinstance(error, sqlite3.Error):
        code = getattr(error, "sqlite_errorcode", None)
        if code is not None and code & 0xFF in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            return DBTransientError(context + "Temporary database contention")
        if code in (sqlite3.SQLITE_CONSTRAINT_UNIQUE, sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY):
            return DBUniqueConstraintError(context + "Unique database constraint violated")
    return DBOperationError(context + str(error))
