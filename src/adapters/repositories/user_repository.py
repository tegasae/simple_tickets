from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import NotFoundError, OptimisticLockError, PersistenceError
from src.adapters.repositories.gateways.user_gateway import UserGateway

from src.adapters.repositories.mappers.user_mapper import UserMapper
from src.adapters.repositories.gateways.employee_gateway import EmployeeGateway

from src.adapters.repositories.gateways.role_gateway import RoleGateway
from src.adapters.repositories.gateways.account_gateway import AccountGateway

from src.domain.employee import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.exceptions import ItemNotFoundError


class UserRepositorySQLite(BaseRepository, UserRepository):



    # ---------- roles ----------

    def _load_roles(self, employee_id: int) -> set[int]:
        rows = self._get_many(
            RoleGateway.SELECT_USER_ROLES,
            ["role_id"],
            {"employee_id": employee_id},
        )
        return {r["role_id"] for r in rows}

    def _replace_roles(self, user: User) -> None:
        self._exec(
            RoleGateway.DELETE_ALL_USER_ROLES,
            {"employee_id": user.employee_id},
        )

        for role_id in user.role_ids():
            self._exec(
                RoleGateway.INSERT_USER_ROLE,
                {"employee_id": user.employee_id, "role_id": role_id},
            )

    # ---------- account ----------

    def _sync_account(self, user: User) -> None:
        params = UserMapper.account_params(user)

        if params is None:
            self._exec(AccountGateway.DELETE_BY_EMPLOYEE, {"employee_id": user.employee_id})
        else:
            self._exec(AccountGateway.UPSERT_BY_EMPLOYEE, params)

    # ---------- reads ----------

    def get(self, user_id: int) -> User:
        row = self._get_one(
            UserGateway.SELECT_BY_ID,
            UserMapper.VARS,
            {"employee_id": user_id},
        )
        if not row:
            raise ItemNotFoundError(f"User {user_id} not found")

        user = UserMapper.row_to_user(row)
        user._role_ids = self._load_roles(user.employee_id)
        return user

    def get_all(self) -> list[User]:
        rows = self._get_many(UserGateway.SELECT_BASE, UserMapper.VARS)

        users: list[User] = []
        for row in rows:
            user = UserMapper.row_to_user(row)
            user._role_ids = self._load_roles(user.employee_id)
            users.append(user)

        return users

    def exists(self, user_id: int) -> bool:
        row = self._get_one(
            UserGateway.EXISTS,
            ["one"],
            {"employee_id": user_id},
        )
        return bool(row)

    def find_by_login(self, *, login: str) -> User:
        row = self._get_one(
            UserGateway.SELECT_BY_LOGIN,
            UserMapper.VARS,
            {"login": login},
        )
        if not row:
            raise ItemNotFoundError(f"User with login '{login}' not found")

        user = UserMapper.row_to_user(row)
        user._role_ids = self._load_roles(user.employee_id)
        return user

    def exist_login(self, login: str) -> bool:
        row = self._get_one(
            UserGateway.EXISTS_LOGIN,
            ["one"],
            {"login": login},
        )
        return bool(row)
    # ---------- persistence ----------

    def save(self, user: User) -> User:
        """
        Saves aggregate:
          - employees (optimistic lock)
          - users
          - users_roles (replace)
          - accounts (sync)
        """
        try:
            if user.employee_id == 0:
                # INSERT employees
                emp_params = UserMapper.employee_params(user)
                emp_params["version"] = 0  # new row
                # EmployeeGateway.INSERT expects is_admin too
                ins_emp = self._exec(EmployeeGateway.INSERT, emp_params)
                user.employee_id = ins_emp.last_row_id

                # INSERT users
                self._exec(UserGateway.INSERT, UserMapper.user_params(user))

            else:
                # UPDATE employees with optimistic lock
                upd_emp = self._exec(EmployeeGateway.UPDATE, UserMapper.employee_params(user))
                if upd_emp.rowcount == 0:
                    if not self.exists(user.employee_id):
                        raise NotFoundError(f"User {user.employee_id} not found")
                    raise OptimisticLockError(
                        f"Optimistic lock failed for User(employee_id={user.employee_id}, version={user.version})"
                    )

                # UPDATE users
                self._exec(UserGateway.UPDATE, UserMapper.user_params(user))

            # Replace roles + sync account
            self._replace_roles(user)
            self._sync_account(user)

            # same style as your admin repo
            user.version += 1
            return user

        except (OptimisticLockError, NotFoundError):
            raise
        except Exception as e:
            raise PersistenceError(f"Failed to save User {user.employee_id}: {e}") from e

    def delete(self, user_id: int) -> None:
        try:
            # reverse dependencies
            self._exec(AccountGateway.DELETE_BY_EMPLOYEE, {"employee_id": user_id})
            self._exec(RoleGateway.DELETE_ALL_USER_ROLES, {"employee_id": user_id})
            self._exec(UserGateway.DELETE, {"employee_id": user_id})
            self._exec(EmployeeGateway.DELETE, {"employee_id": user_id})

        except Exception as e:
            raise PersistenceError(f"Failed to delete User {user_id}: {e}") from e

