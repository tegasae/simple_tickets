# src/adapters/repositories/mappers/department_mapper.py

from datetime import datetime

from src.domain.department import Department


class DepartmentMapper:

    @staticmethod
    def row_to_department(row: dict) -> Department:
        department = Department.restore(
            department_id=row["department_id"],
            name=row["name"],
            enabled=bool(row["enabled"]),
            date_created=DepartmentMapper._parse_date_created(row["date_created"]),
            version=DepartmentMapper._parse_version(row["version"]),
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

    @staticmethod
    def _parse_version(value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_date_created(value) -> datetime:
        if not value:
            return datetime.now()

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now()