from dataclasses import dataclass
from typing import Iterable, Type, Generic

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.gateways.role_gateway import RoleGateway
from src.domain.exceptions import ItemNotFoundError
from src.domain.rbac.role_repository import RoleRepository
from src.domain.rbac.role_new import Role
from src.domain.rbac.typevar import P
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError
from src.adapters.repositories.mappers.role_mapper import RoleMapper

@dataclass
class RoleRepositorySQLite(BaseRepository,RoleRepository[P], Generic[P]):



    conn: Connection
    permission_cls: Type[P]
    is_admin: bool = True




    # -------------------------
    # Add
    # -------------------------

    def add(self, role: Role[P]) -> Role[P]:

        try:
            er=self._exec(RoleGateway.INSERT_ROLE,RoleMapper.role_params(role,is_admin=self.is_admin))
            return Role(
                role_id=er.last_row_id,
                name=role.name,
                permissions=role.permissions,
                description=role.description,
                is_system_role=role.is_system_role,
                date_created=role.date_created,
                version=role.version,
            )

        except Exception as e:
            raise DBOperationError(f"Failed to add role: {e}")

    # -------------------------
    # Get
    # -------------------------

    def get(self, role_id: int) -> Role[P]:
        row = self._get_one(
            RoleGateway.SELECT_BY_ID,
            RoleMapper.VARS,
            {"is_admin":self.is_admin,"role_id": role_id},
        )


        if not row:
            raise ItemNotFoundError(f"The role {role_id} not found" )

        try:
            role=RoleMapper.row_to_role(row, self.permission_cls)
        except AttributeError as e:
            raise DBOperationError(f"Role {role_id} not valid") from e
        return role

    # -------------------------
    # All roles
    # -------------------------

    def all(self) -> Iterable[Role[P]]:

        rows = self._get_many(RoleGateway.SELECT_BASE, var=RoleMapper.VARS,params={"is_admin":self.is_admin})

        roles: list[Role[P]] = []
        for row in rows:
            if not row["permissions"]:
                row["permissions"] = ""

            role = RoleMapper.row_to_role(row,self.permission_cls)

            roles.append(role)

        return roles

    # -------------------------
    # Delete
    # -------------------------

    def delete(self, role_id: int):
        try:
            self._exec(RoleGateway.DELETE_ROLE,params={"role_id": role_id,"is_admin":self.is_admin})
        except Exception as e:
            raise DBOperationError(f"Failed to delete role {role_id}: {e}")

    def is_assigned(self, role_id: int) -> bool:
        row = self._get_one(
            RoleGateway.EXIST,
            ["one"],
            {"role_id": role_id},
        )

        return row is not None