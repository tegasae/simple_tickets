from dataclasses import field, dataclass
from typing import Iterable, TypeVar

from src.domain.rbac.permissions import PermissionBase

T = TypeVar("T", bound=PermissionBase)

@dataclass(kw_only=True)
class RoleDTO:
    actor_admin_id: int
    role_id:int=0
    name: str
    permissions: frozenset = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False




@dataclass(kw_only=True, frozen=True)
class RoleResponseDTO:
    role_id:int
    name:str
    permissions: frozenset = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
