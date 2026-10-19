# src/adapters/repositories/mappers/department_mapper.py


from src.adapters.repositories.mappers.auxiliary import dt_from_sqlite_not_none
from src.domain.department import Department


class DepartmentMapper:
    VARS = [
        "department_id",
        "name",
        "enabled",
        "version",
        "date_created",
    ]
    @staticmethod
    def row_to_department(row: dict) -> Department:
        department = Department.rehydrate(
            department_id=row["department_id"],
            name=row["name"],
            enabled=bool(row["enabled"]),
            date_created=dt_from_sqlite_not_none(row["date_created"]),
            version=int(row["version"]) or 0,
        )

        return department

    @staticmethod
    def params(department: Department) -> dict:
        return {
            "department_id": department.department_id,
            "name": str(department.name),
            "enabled": int(department.enabled),
            "version": department.version,
            "date_created": department.date_created.isoformat(),
        }

