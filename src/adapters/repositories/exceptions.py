from __future__ import annotations


class RepositoryError(Exception):
    """Base class for repository-layer errors."""


class NotFoundError(RepositoryError):
    """Raised when an entity is not found in persistence."""


class OptimisticLockError(RepositoryError):
    """
    Raised when optimistic locking fails.
    Typical reason: version mismatch (someone updated the row).
    """


class PersistenceError(RepositoryError):
    """Raised when persistence operation fails (SQL error, constraint, etc.)."""
