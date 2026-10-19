#src/domain/rbac/typevar.py

from typing import TypeVar
from src.domain.rbac.permissions import PermissionBase
P = TypeVar("P", bound=PermissionBase)
