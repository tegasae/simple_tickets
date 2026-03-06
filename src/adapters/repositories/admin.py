from __future__ import annotations

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import NotFoundError, OptimisticLockError, PersistenceError
from src.adapters.repositories.gateways.account_gateway import AccountGateway
from src.adapters.repositories.gateways.admin_gateway import AdminGateway
from src.adapters.repositories.gateways.employee_gateway import EmployeeGateway
from src.adapters.repositories.gateways.role_gateway import RoleGateway
from src.adapters.repositories.mappers.admin_mapper import AdminMapper

from src.domain.employee import Admin
from src.domain.repositories.admin_repository import AdminRepository


class AdminRepositorySQLite(BaseRepository, AdminRepository):
    """
    Admin aggregate repository (SQLite) using:
      - BaseRepository helpers
      - Gateways (SQL)
      - Mapper (row<->entity)

    Optimistic lock is enforced on employees.version for updates.
    """



    # -------------------------
    # Roles
    # -------------------------

    def _load_roles(self, employee_id: int) -> set[int]:
        rows = self._get_many(
            RoleGateway.SELECT_ADMIN_ROLE_IDS,
            var=["role_id"],
            params={"employee_id": employee_id},
        )
        return {int(r["role_id"]) for r in rows}

    def _replace_roles(self, admin: Admin) -> None:
        self._exec(RoleGateway.DELETE_ALL_FOR_ADMIN, {"employee_id": admin.employee_id})

        role_ids = set(admin.role_ids())
        if not role_ids:
            return

        for role_id in role_ids:
            self._exec(
                RoleGateway.INSERT_ADMIN_ROLE,
                {"employee_id": admin.employee_id, "role_id": int(role_id)},
            )

    # -------------------------
    # Account
    # -------------------------

    def _sync_account(self, admin: Admin) -> None:
        params = AdminMapper.account_params(admin)
        if params is None:
            self._exec(AccountGateway.DELETE_BY_EMPLOYEE, {"employee_id": admin.employee_id})
        else:
            self._exec(AccountGateway.UPSERT_BY_EMPLOYEE, params)

    # -------------------------
    # Reads
    # -------------------------

    def get(self, admin_id: int) -> Admin:
        row = self._get_one(AdminGateway.SELECT_BY_ID, var=AdminMapper.VARS, params={"employee_id": admin_id})
        if not row:
            raise NotFoundError(f"Admin {admin_id} not found")

        admin = AdminMapper.row_to_admin(row)
        admin._role_ids = self._load_roles(admin.employee_id)
        return admin

    def get_all(self) -> list[Admin]:
        rows = self._get_many(AdminGateway.SELECT_BASE, var=AdminMapper.VARS)
        admins: list[Admin] = []
        for row in rows:
            admin = AdminMapper.row_to_admin(row)
            admin._role_ids = self._load_roles(admin.employee_id)
            admins.append(admin)
        return admins

    def exists(self, admin_id: int) -> bool:
        return self._exists(AdminGateway.EXISTS, {"employee_id": admin_id})

    def find_by_login(self, *, login: str) -> Admin:
        row = self._get_one(AdminGateway.SELECT_BY_LOGIN, var=AdminMapper.VARS, params={"login": login})
        if not row:
            raise NotFoundError(f"Admin with login '{login}' not found")

        admin = AdminMapper.row_to_admin(row)
        admin._role_ids = self._load_roles(admin.employee_id)
        return admin

    # -------------------------
    # Writes
    # -------------------------

    def save(self, admin: Admin) -> Admin:
        """
        Save the whole aggregate:
          employees + admins + admins_roles + accounts

        Optimistic lock:
          - UPDATE employees WHERE version=:version
          - if rowcount==0 => OptimisticLockError
          - if success => in DB version increments, so we increment admin.version in memory too
        """
        try:
            if admin.employee_id == 0:
                # Create new
                emp_params = AdminMapper.employee_params(admin)
                emp_params["is_admin"] = 1

                ins = self._exec(EmployeeGateway.INSERT, emp_params)
                admin.employee_id = ins.last_row_id
                admin.version = 0  # first version in DB is 0

                self._exec(AdminGateway.INSERT, AdminMapper.admin_params(admin))

                self._replace_roles(admin)
                self._sync_account(admin)
                return admin

            # Update existing with optimistic lock

            upd = self._exec(
                EmployeeGateway.UPDATE,
                AdminMapper.employee_params(admin),
            )

            if upd.rowcount == 0:
                # Check if admin still exists
                if not self.exists(admin.employee_id):
                    raise NotFoundError(f"Admin {admin.employee_id} no longer exists")

                # Otherwise version mismatch
                raise OptimisticLockError(
                    f"Optimistic lock failed for Admin(employee_id={admin.employee_id}, "
                    f"version={admin.version})"
                )



            self._exec(AdminGateway.UPDATE, AdminMapper.admin_params(admin))

            self._replace_roles(admin)
            self._sync_account(admin)

            # DB incremented version => mirror it in memory
            admin.version += 1
            return admin

        except OptimisticLockError:
            raise
        except NotFoundError:
            raise
        except PersistenceError:
            raise
        except Exception as e:
            raise PersistenceError(f"Failed to save Admin(employee_id={admin.employee_id}): {e}") from e

    def delete(self, admin_id: int) -> None:
        """
        Hard delete aggregate in safe order:
          accounts -> admins_roles -> admins -> employees(is_admin=1)

        Note:
          employees delete includes is_admin=1 guard to prevent deleting user employees by mistake.
        """
        try:
            self._exec(AccountGateway.DELETE_BY_EMPLOYEE, {"employee_id": admin_id})
            self._exec(RoleGateway.DELETE_ALL_FOR_ADMIN, {"employee_id": admin_id})
            self._exec(AdminGateway.DELETE, {"employee_id": admin_id})
            self._exec(EmployeeGateway.DELETE_ADMIN_EMPLOYEE, {"employee_id": admin_id})
        except Exception as e:
            raise PersistenceError(f"Failed to delete Admin(employee_id={admin_id}): {e}") from e

    # -------------------------
    # Optional direct role ops (handy, but DDD-pure style is: get->mutate->save)
    # -------------------------

    def grant_role(self, *, employee_id: int, role_id: int) -> None:
        # avoid duplicates (PK handles too, but error is annoying)
        if self._exists(RoleGateway.EXISTS_ONE, {"employee_id": employee_id, "role_id": role_id}):
            return
        self._exec(RoleGateway.INSERT_ADMIN_ROLE, {"employee_id": employee_id, "role_id": role_id})

    def revoke_role(self, *, employee_id: int, role_id: int) -> None:
        self._exec(RoleGateway.DELETE_ONE, {"employee_id": employee_id, "role_id": role_id})

    def get_role_ids(self, *, employee_id: int) -> set[int]:
        return self._load_roles(employee_id)

    # -------------------------
    # Optional direct account ops
    # -------------------------

    def set_no_account(self, *, employee_id: int) -> None:
        self._exec(AccountGateway.DELETE_BY_EMPLOYEE, {"employee_id": employee_id})

    def exist_login(self, login: str) -> bool:
        row = self._get_one(
            AdminGateway.EXISTS_LOGIN,
            ["one"],
            {"login": login},
        )
        return bool(row)