# src/application/dto/roles_dto.py


from dataclasses import dataclass, field

from src.application.exceptions import ApplicationValidateError


@dataclass(kw_only=True)
class RoleDTO:
    actor_admin_id: int
    role_id: int = 0
    name: str = ""
    permissions: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False

    def __post_init__(self):
        if self.role_id<0:
            raise ApplicationValidateError("Role id must be positive")


@dataclass(kw_only=True, frozen=True)
class RoleResponseDTO:
    role_id: int
    name: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False