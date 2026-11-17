# src/domain/department.py

from dataclasses import dataclass, field, InitVar
from datetime import datetime
from typing import Self

from src.domain.exceptions import ItemValidationError, DomainOperationError
from src.domain.value_objects import Name

_EMPTY_DEPARTMENT_TOKEN = object()
@dataclass
class Department:
    """
    Department domain entity.

    Department is used to group Admins and Tickets.

    Rules:
    - Admin can belong to one department or to no department.
    - Ticket can belong to one department or to no department.
    - Executor assignment requires Admin.department_id == Ticket.department_id.
    """

    department_id: int
    name: Name
    enabled: bool = True
    date_created: datetime = field(default_factory=datetime.now)
    version: int = 0
    _is_empty: bool = field(default=False, init=False, repr=False,compare=False)
    _empty_token: InitVar[object | None] = None

    @classmethod
    def create(
        cls,
        *,

        name: str,
        enabled: bool = True,
    ) -> Self:

        try:
            return cls(
                department_id=0,
                name=Name(name),
                enabled=enabled,
            )
        except ValueError as e:
            raise ItemValidationError(f"Department validation failed: {e}") from e

    @classmethod
    def rehydrate(
        cls,
        *,
        department_id: int,
        name: str,
        enabled: bool,
        date_created: datetime,
        version: int,
    ) -> Self:
        """
        Restore Department from database.

        Repository mapper should use this method.
        """

        try:
            return cls(
                department_id=department_id,
                name=Name(name),
                enabled=enabled,
                date_created=date_created,
                version=version,
            )
        except ValueError as e:
            raise ItemValidationError(f"Department validation failed: {e}") from e

    def __post_init__(self,_empty_token: object | None) -> None:
        if _empty_token is _EMPTY_DEPARTMENT_TOKEN:
            if self.department_id != 0:
                raise ItemValidationError(
                    "Invalid empty department"
                )

            self._is_empty = True
            return

        if _empty_token is not None:
            raise ItemValidationError(
                "Invalid empty department token"
            )

        if self.department_id < 0:
            raise ItemValidationError(
                "Department ID cannot be negative"
            )

        if self.version < 0:
            raise ItemValidationError(
                "Department version cannot be negative"
            )

    @classmethod
    def create_empty(cls) -> Self:
        return cls(
            department_id=0,
            name=Name("--"),
            enabled=True,
            _empty_token=_EMPTY_DEPARTMENT_TOKEN
        )


    def is_empty(self) -> bool:
        return self._is_empty


    def rename(self, name: str) -> None:
        self._ensure_enabled()

        try:
            self.name = Name(name)
        except ValueError as e:
            raise ItemValidationError(f"Invalid department name: {e}") from e

    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True

    def ensure_enabled(self) -> None:
        self._ensure_enabled()

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise DomainOperationError("Department is disabled")


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Department):
            return False
        return self.department_id == other.department_id

    def __hash__(self) -> int:
        return hash(self.department_id)

    def __str__(self) -> str:
        return f"Department(id={self.department_id}, name={self.name})"