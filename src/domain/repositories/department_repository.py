# src/domain/repositories/department_repository.py

from abc import ABC, abstractmethod

from src.domain.department import Department


class DepartmentRepository(ABC):

    @abstractmethod
    def get(self, department_id: int) -> Department:
        raise NotImplementedError()

    @abstractmethod
    def get_all(self) -> list[Department]:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, department_id: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def save(self, department: Department) -> Department:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, department_id: int) -> None:
        raise NotImplementedError()