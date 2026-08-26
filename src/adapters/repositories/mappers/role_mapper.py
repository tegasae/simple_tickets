# src/adapters/repositories/mappers/role_mapper.py

from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Iterable


from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P


def _dt_to_sqlite_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


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
    def role_params(
        role: Role[P],
        *,
        is_admin: bool = False,
    ) -> dict:
        return {
            "role_id": role.role_id,
            "name": role.name,
            "permissions": RoleMapper.permissions_to_string(role.permissions),
            "description": role.description,
            "is_system_role": role.is_system_role,
            "date_created": _dt_to_sqlite_iso(role.date_created),
            "version": role.version if role.version is not None else 0,
            "is_admin": is_admin,
        }

    @staticmethod
    def row_to_role(
        row: dict,
        permission_cls: type[P],
    ) -> Role[P]:
        permissions = _parse_permissions(
            row["permissions"],
            permission_cls,
        )

        return Role(
            role_id=row["role_id"],
            name=row["name"],
            permissions=permissions,
            description=row["description"] or "",
            is_system_role=bool(row["is_system_role"]),
            date_created=_parse_date(row["date_created"]),
            version=row["version"] or 0,
        )

    @staticmethod
    def permissions_to_string(
            permissions: Iterable[P],
    ) -> str:
        values: list[str] = [
            str(permission.value)
            for permission in permissions
        ]

        values.sort()

        return ",".join(values)

def _parse_date(
    date_value: str | None,
) -> datetime:
    if not date_value:
        return datetime.now(timezone.utc)

    return datetime.fromisoformat(date_value)


def _parse_permissions(
    value: str | None,
    permission_cls: type[P],
) -> frozenset[P]:
    if not value:
        return frozenset()

    permissions: set[P] = set()

    for raw_permission in value.split(","):
        permission_value = raw_permission.strip()

        if not permission_value:
            continue

        permissions.add(
            permission_cls(permission_value)
        )

    return frozenset(permissions)