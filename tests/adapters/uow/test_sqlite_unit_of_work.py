# tests/adapters/uow/test_sqlite_unit_of_work.py

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork


@dataclass
class SpyConnection:
    begin_calls: int = 0
    commit_calls: int = 0
    rollback_calls: int = 0

    transaction_active: bool = False

    fail_on_begin: bool = False
    fail_on_commit: bool = False
    fail_on_rollback: bool = False

    def begin_transaction(self) -> None:
        self.begin_calls += 1

        if self.fail_on_begin:
            raise RuntimeError("begin failed")

        self.transaction_active = True

    def commit(self) -> None:
        self.commit_calls += 1

        if self.fail_on_commit:
            raise RuntimeError("commit failed")

        self.transaction_active = False

    def rollback(self) -> None:
        self.rollback_calls += 1

        if self.fail_on_rollback:
            raise RuntimeError("rollback failed")

        self.transaction_active = False


@pytest.fixture
def connection() -> SpyConnection:
    return SpyConnection()


@pytest.fixture
def uow(connection: SpyConnection) -> SQLiteUnitOfWork:
    return SQLiteUnitOfWork(connection=connection)


# --------------------------------
# Repository wiring
# --------------------------------


def test_all_repositories_use_same_connection(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    assert uow.admins.conn is connection
    assert uow.users.conn is connection
    assert uow.clients.conn is connection
    assert uow.tickets.conn is connection
    assert uow.user_tickets.conn is connection
    assert uow.departments.conn is connection
    assert uow.roles_admin.conn is connection
    assert uow.roles_user.conn is connection


# --------------------------------
# Normal successful flow
# --------------------------------


def test_enter_starts_transaction(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    assert not uow.is_active()
    assert not connection.transaction_active

    with uow as current_uow:
        assert current_uow is uow
        assert uow.is_active()
        assert connection.transaction_active

        assert connection.begin_calls == 1
        assert connection.commit_calls == 0
        assert connection.rollback_calls == 0

    assert not uow.is_active()
    assert not connection.transaction_active


def test_successful_context_auto_commits_once(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with uow:
        pass

    assert connection.begin_calls == 1
    assert connection.commit_calls == 1
    assert connection.rollback_calls == 0

    assert not connection.transaction_active
    assert not uow.is_active()


# --------------------------------
# Explicit completion
# --------------------------------


def test_explicit_commit_is_not_repeated_on_context_exit(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with uow:
        uow.commit()

        assert not uow.is_active()
        assert not connection.transaction_active

    assert connection.begin_calls == 1
    assert connection.commit_calls == 1
    assert connection.rollback_calls == 0


def test_explicit_rollback_prevents_auto_commit(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with uow:
        uow.rollback()

        assert not uow.is_active()
        assert not connection.transaction_active

    assert connection.begin_calls == 1
    assert connection.commit_calls == 0
    assert connection.rollback_calls == 1


def test_commit_outside_active_context_raises(
    uow: SQLiteUnitOfWork,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="active UnitOfWork",
    ):
        uow.commit()


def test_rollback_outside_active_context_is_noop(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    uow.rollback()

    assert connection.rollback_calls == 0
    assert not uow.is_active()


# --------------------------------
# Error flow
# --------------------------------


def test_exception_in_context_rolls_back_and_propagates(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with pytest.raises(
        ValueError,
        match="domain failure",
    ):
        with uow:
            raise ValueError("domain failure")

    assert connection.begin_calls == 1
    assert connection.commit_calls == 0
    assert connection.rollback_calls == 1

    assert not connection.transaction_active
    assert not uow.is_active()


def test_exception_after_explicit_commit_is_propagated_without_rollback(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with pytest.raises(
        ValueError,
        match="failure after commit",
    ):
        with uow:
            uow.commit()
            raise ValueError("failure after commit")

    assert connection.begin_calls == 1
    assert connection.commit_calls == 1
    assert connection.rollback_calls == 0

    assert not connection.transaction_active
    assert not uow.is_active()


def test_commit_error_propagates_and_uow_state_is_reset(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    connection.fail_on_commit = True

    with pytest.raises(
        RuntimeError,
        match="commit failed",
    ):
        with uow:
            pass

    assert connection.begin_calls == 1
    assert connection.commit_calls == 1
    assert connection.rollback_calls == 0

    assert not uow.is_active()


# --------------------------------
# Nesting
# --------------------------------


def test_nested_context_is_rejected(
    uow: SQLiteUnitOfWork,
    connection: SpyConnection,
) -> None:
    with uow:
        with pytest.raises(
            RuntimeError,
            match="nest",
        ):
            with uow:
                pass

        assert uow.is_active()
        assert connection.transaction_active

    assert connection.begin_calls == 1
    assert connection.commit_calls == 1
    assert connection.rollback_calls == 0

    assert not uow.is_active()
    assert not connection.transaction_active