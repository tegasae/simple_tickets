# ============================
# src/domain/permissions/base.py
# ============================
from __future__ import annotations

from enum import StrEnum
from typing import Self


class PermissionBase(StrEnum):
    """
    Base class for all permission enums.
    Permissions are stable string identifiers.
    """

    @classmethod
    def from_value(cls, value: str) -> Self:
        """Restore permission from stored string. Raises ValueError if invalid."""
        return cls(value)
