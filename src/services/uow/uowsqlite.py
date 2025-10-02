from abc import ABC, abstractmethod
from typing import ContextManager
import logging

from src.adapters import repository, repositorysqlite
from utils.db.connect import Connection

logger = logging.getLogger(__name__)


class AbstractUnitOfWork(ABC, ContextManager):
    admins_repository: repository.AdminRepositoryAbstract
    """
    Abstract base class that combines ABC and ContextManager
    All concrete implementations must follow this interface
    """

    @abstractmethod
    def __enter__(self) -> 'AbstractUnitOfWork':
        """Start transaction - must return self"""
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Handle transaction completion"""
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit transaction"""
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Rollback transaction"""
        raise NotImplementedError

    @property
    @abstractmethod
    def admins(self)-> repository.AdminRepositoryAbstract:
        """Admin repository access"""
        raise NotImplementedError

    @abstractmethod
    def is_active(self) -> bool:
        """Check if transaction is active"""
        raise NotImplementedError


class SqliteUnitOfWork(AbstractUnitOfWork):
    """
    Concrete implementation for SQLite database
    Inherits from AbstractUnitOfWork and implements all abstract methods
    """

    def __init__(self, connection:Connection):
        self.connection = connection
        self._admins_repo = None
        self._active = False
        self._committed = False
        self.admins_repository = repositorysqlite.SQLiteAdminRepository(conn=self.connection)

    # ========== ContextManager Methods ==========
    def __enter__(self) -> 'SqliteUnitOfWork':
        """Start SQLite transaction"""
        self.connection.begin_transaction()
        self._active = True
        self._committed = False
        logger.debug("SQLite transaction started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Handle SQLite transaction completion"""
        self._active = False

        try:
            if exc_type is not None:
                # Exception occurred - auto rollback
                self.rollback()
                logger.debug("Auto-rollback due to exception")
            elif not self._committed:
                # No explicit commit - safety rollback
                self.rollback()
                logger.warning("Auto-rollback: no commit called")
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            # Don't mask original exception
            if exc_type is None:
                raise

        return False  # Re-raise original exception

    # ========== Business Methods ==========
    def commit(self) -> None:
        """Commit SQLite transaction"""
        if not self._active:
            raise RuntimeError("No active transaction to commit")

        self.connection.commit()
        self._committed = True
        logger.info("SQLite transaction committed")

    def rollback(self) -> None:
        """Rollback SQLite transaction"""
        if self._active:
            self.connection.rollback()
            self._committed = True  # Mark as handled
            logger.info("SQLite transaction rolled back")

    @property
    def admins(self)->repository.AdminRepositoryAbstract:

        # if self._admins_repo is None:
        #    from src.adapters.repository_sqlite import SQLiteAdminRepository
        #    self._admins_repo = SQLiteAdminRepository(self.connection)
        # return self._admins_repo
        return self.admins_repository

    def is_active(self) -> bool:
        """Check if SQLite transaction is active"""
        return self._active
