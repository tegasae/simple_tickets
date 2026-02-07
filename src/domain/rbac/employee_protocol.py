from __future__ import annotations

from typing import Protocol, FrozenSet


class HasRoleIds(Protocol):
    """Entity protocol: RBAC needs role ids + mutation."""
    def role_ids(self) -> FrozenSet[int]: ...
    def grant_role(self, role_id: int) -> None: ...
    def revoke_role(self, role_id: int) -> None: ...
