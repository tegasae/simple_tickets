# src/application/dto/department_dto.py

from dataclasses import dataclass
from datetime import datetime

from src.application.exceptions import ApplicationValidateError


@dataclass(frozen=True, kw_only=True)
class DepartmentDTO:
    actor_admin_id: int = 0
    department_id: int = 0
    name: str = ""
    enabled: bool = True

    def __post_init__(self):
        if self.actor_admin_id<0:
            raise ApplicationValidateError(f"The actor admin id must be positive in department DTO")

        if self.department_id < 0:
            raise ApplicationValidateError("The department id must be positive department DTO")

        if not self.name.strip():
            raise ApplicationValidateError("The name cannot be empty in department DTO")



@dataclass(frozen=True, kw_only=True)
class DepartmentResponseDTO:
    department_id: int
    name: str
    enabled: bool
    date_created: datetime
