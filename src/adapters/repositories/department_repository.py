# src/adapters/repositories/department_repository.py

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import (
    OptimisticLockError,
    NotFoundError, PersistenceError,
)

from src.adapters.repositories.gateways.department_gateway import DepartmentGateway
from src.adapters.repositories.mappers.department_mapper import DepartmentMapper

from src.domain.department import Department
from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError
from src.domain.repositories.department_repository import DepartmentRepository


class DepartmentRepositorySQLite(BaseRepository, DepartmentRepository):

    VARS = [
        "department_id",
        "name",
        "enabled",
        "version",
        "date_created",
    ]

    # -------------------------
    # Reads
    # -------------------------

    def get(self, department_id: int) -> Department:
        row = self._get_one(
            DepartmentGateway.SELECT_BY_ID,
            var=self.VARS,
            params={"department_id": department_id},
        )

        if not row:
            raise ItemNotFoundError(f"Department {department_id} not found")

        return DepartmentMapper.row_to_department(row)

    def get_all(self) -> list[Department]:
        rows = self._get_many(
            DepartmentGateway.SELECT_BASE,
            var=self.VARS,
        )

        return [
            DepartmentMapper.row_to_department(row)
            for row in rows
        ]

    def exists(self, department_id: int) -> bool:
        return self._exists(
            DepartmentGateway.EXISTS,
            {"department_id": department_id},
        )

    # -------------------------
    # Writes
    # -------------------------

    def save(self, department: Department) -> Department:
        try:
            if department.department_id == 0:
                result = self._exec(
                    DepartmentGateway.INSERT,
                    DepartmentMapper.params(department),
                )

                department.department_id = result.last_row_id
                department.version = 0

                return department

            upd = self._exec(
                DepartmentGateway.UPDATE,
                DepartmentMapper.params(department),
            )

            if upd.rowcount == 0:
                if not self.exists(department.department_id):
                    raise NotFoundError(
                        f"Department {department.department_id} no longer exists"
                    )

                raise OptimisticLockError(
                    f"Department {department.department_id} version mismatch"
                )
        except PersistenceError:
            raise ItemAlreadyExistsError(item_name=str(department.name))

        department.version += 1

        return department

    def delete(self, department_id: int) -> None:
        if not self.exists(department_id):
            raise NotFoundError(f"Department {department_id} not found")

        self._exec(
            DepartmentGateway.DELETE,
            {"department_id": department_id},
        )