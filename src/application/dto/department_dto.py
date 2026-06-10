# src/application/dto/department_dto.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class DepartmentDTO:
    actor_admin_id: int = 0
    department_id: int = 0
    name: str = ""
    enabled: bool = True



@dataclass(frozen=True, kw_only=True)
class DepartmentResponseDTO:
    department_id: int
    name: str
    enabled: bool
    date_created: datetime
