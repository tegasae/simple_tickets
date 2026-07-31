# src/application/dto/roles_dto.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from src.domain.rbac.permissions import PermissionBase


T = TypeVar("T", bound=PermissionBase)


@dataclass(kw_only=True)
class RoleDTO(Generic[T]):
    actor_admin_id: int
    role_id: int = 0
    name: str = ""
    permissions: frozenset[T] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False



@dataclass(kw_only=True, frozen=True)
class RoleResponseDTO(Generic[T]):
    role_id: int
    name: str
    permissions: frozenset[T] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False