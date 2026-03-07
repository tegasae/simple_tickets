from datetime import datetime
from typing import Iterable, Type

from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P


class RoleMapper:
    VARS = [
        "role_id",
        "name",
        "permissions",
        "description",
        "is_system_role",
        "date_created",
        "is_admin",
        "version",
    ]

    @staticmethod
    def role_params(role: Role,is_admin=0) -> dict:
        return {
            "role_id": role.role_id,
            "name": role.name,
            "permissions": RoleMapper.permissions_to_string(role.permissions),
            "description": role.description,
            "is_system_role": role.is_system_role,
            "version": role.version if role.version is not None else 0,
            "is_admin":is_admin

        }
    @staticmethod
    def row_to_role(row: dict,permission_cls) -> Role[P]:
        permissions = _parse_permissions(
            row["permissions"],
            permission_cls,
        )

        role = Role(
            role_id=row["role_id"],
            name=row["name"],
            permissions=permissions,
            description=row["description"],
            is_system_role=bool(row["is_system_role"]),
            date_created=_parse_date(row["date_created"]),
            version=row["version"] or 0,
        )

        return role
    @staticmethod
    def permissions_to_string(perms: Iterable[P]) -> str:
        return ",".join(str(p) for p in perms)


def _parse_date(date_value: str | None) -> datetime:

    if not date_value:
        return datetime.now()

    try:
        return datetime.fromisoformat(date_value)
    except ValueError:
        return datetime.now()


def _parse_permissions(value: str, permission_cls: Type[P]) -> frozenset[P]:
    return frozenset(permission_cls(p) for p in value.split(",") if p)


# -------------------------
    # Row mapper
    # -------------------------


