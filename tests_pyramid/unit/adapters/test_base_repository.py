from __future__ import annotations

from contextlib import contextmanager

import pytest

from src.adapters.repositories.base_repository import BaseRepository, ExecResult
from src.adapters.repositories.exceptions import PersistenceError

pytestmark = pytest.mark.unit


class FakeQuery:
    def __init__(self, *, one=None, many=None, last_id=0, count=0, error: Exception | None = None):
        self.one = one
        self.many = many
        self.last_id = last_id
        self.count = count
        self.error = error

    def __enter__(self):
        if self.error:
            raise self.error
        return self

    def __exit__(self, *args):
        return False

    def get_one_result(self, params=None):
        if self.error:
            raise self.error
        return self.one

    def get_result(self, params=None):
        if self.error:
            raise self.error
        return self.many

    def set_result(self, params=None):
        if self.error:
            raise self.error
        return self.last_id


class FakeConnection:
    def __init__(self, query: FakeQuery):
        self.query = query
        self.calls = []

    def create_query(self, sql, var=None, params=None):
        self.calls.append((sql, var, params))
        return self.query


def test_base_repository_get_one_many_exec_and_exists() -> None:
    conn = FakeConnection(FakeQuery(one={"one": 1}, many=[{"x": 1}], last_id=7, count=2))
    repo = BaseRepository(conn)
    assert repo._get_one("select") == {"one": 1}
    assert repo._get_many("select") == [{"x": 1}]
    assert repo._exec("update") == ExecResult(last_row_id=7, rowcount=2)
    assert repo._exists("select 1") is True


def test_base_repository_exists_false_for_empty_row() -> None:
    repo = BaseRepository(FakeConnection(FakeQuery(one={})))
    assert repo._exists("select 1") is False


def test_base_repository_wraps_generic_adapter_errors() -> None:
    repo = BaseRepository(FakeConnection(FakeQuery(error=RuntimeError("db boom"))))
    with pytest.raises(PersistenceError, match="db boom"):
        repo._get_one("select")
    with pytest.raises(PersistenceError, match="db boom"):
        repo._get_many("select")
    with pytest.raises(PersistenceError, match="db boom"):
        repo._exec("update")
