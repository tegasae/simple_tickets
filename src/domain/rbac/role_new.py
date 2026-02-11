from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, FrozenSet

from src.domain.rbac.role import P


@dataclass(frozen=True)
class Role(Generic[P]):
    role_id: int                 # DB primary key
    name: str                    # human-readable (may change)
    permissions: FrozenSet[P] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_permission(self, permission: P) -> bool:
        return permission in self.permissions
