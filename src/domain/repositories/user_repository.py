from abc import ABC, abstractmethod

from src.domain.employee import User


class UserRepository(ABC):
    """
    Optional narrower repository if you prefer using subtype-specific repos.
    Useful when User and Admin are stored differently.

    If you keep one table + discriminator, you can skip this interface
    and use only EmployeeRepository.
    """

    @abstractmethod
    def get(self, user_id: int) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def get_all_by_client(self,client_id:int)->list[User]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, user: User)->User:
        raise NotImplementedError


    @abstractmethod
    def delete(self, user_id: int):
        raise NotImplementedError
