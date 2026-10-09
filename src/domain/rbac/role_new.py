#src/domain/rbac/role_new.py



from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, Self

from src.domain.exceptions import ItemValidationError, DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.typevar import P
from src.domain.value_objects import Name


@dataclass(kw_only=True)
class Role(Generic[P]):
    role_id: int=0                 # DB primary key
    name: Name                    # human-readable (may change)
    permissions: frozenset[P] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 0

    def __post_init__(self):
        if self.role_id<0:
            raise ItemValidationError("role_id must be positive")
        if not self.permissions:
            raise DomainOperationError("Role must have at least one permission")

    @classmethod
    def create(cls,name:str,
               permissions:frozenset[P],
               description:str="",
               is_system_role:bool=False)->Self:
        return cls(name=Name(name),
                   permissions=permissions,
                   description=description,
                   is_system_role=is_system_role)


    @classmethod
    def rehydrate(cls, role_id:int,
                  name: str,
                  date_created: datetime,
                  version:int,
                  permissions: frozenset[P],
                  description: str = "",
                  is_system_role: bool = False) -> Self:

        return cls(role_id=role_id,
                   name=Name(name),
                   permissions=permissions,
                   description=description,
                   is_system_role=is_system_role,
                   date_created=date_created,
                   version=version)

    def has_permission(self, permission: P) -> bool:
        return permission in self.permissions

    def __hash__(self) -> int:
        return hash(self.role_id)

@dataclass
class AdminRole(Role[AdminPermission]):
    """Role that can only contain admin permissions."""

    def __post_init__(self):
        super().__post_init__()
        # Validate at creation time
        for perm in self.permissions:
            if not isinstance(perm, AdminPermission):
                raise ValueError(f"AdminRole can only contain AdminPermissions, got {type(perm)}")

@dataclass
class UserRole(Role[UserPermission]):
    """Role that can only contain user permissions."""

    def __post_init__(self):
        super().__post_init__()

        for perm in self.permissions:
            if not isinstance(perm, UserPermission):
                raise ValueError(f"UserRole can only contain UserPermissions, got {type(perm)}")
@dataclass
class RoleStore(Generic[P]):
    roles: set[Role[P]] = field(default_factory=set)
    def put_role(self, role: Role[P]) -> None:
        self.roles.add(role)

    def delete_role(self, role: Role[P]) -> None:
        self.roles.remove(role)

    def check_role(self, role: Role[P]) -> bool:
        return role in self.roles
