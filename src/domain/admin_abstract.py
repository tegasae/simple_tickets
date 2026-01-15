from abc import abstractmethod, ABC

from src.domain.permissions.rbac import RoleRegistry


class AdminAbstract(ABC):
    """Abstract base class for all Admin types"""
    """Класс абстрактный Админ. Абстрактным сделан для реализации обычного Admin и AdminEmpty. 
    AdminEmpty используется вместо использования None значений. В дальнейшем на базе этого класса будет реализован 
    класс User, который будет предком как для Admin, так и для представителей клиентов"""
    created_clients = 0
    @property
    @abstractmethod
    def admin_id(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def has_permission(self, permission: Permission, role_registry: RoleRegistry) -> bool:
        raise NotImplementedError

    @admin_id.setter
    @abstractmethod
    def admin_id(self, value: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @name.setter
    @abstractmethod
    def name(self, value: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def email(self) -> str:
        raise NotImplementedError

    @email.setter
    @abstractmethod
    def email(self, value: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool):
        raise NotImplementedError

    @property
    @abstractmethod
    def date_created(self) -> datetime:
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __bool__(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def verify_password(self, password: str) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def password(self):
        raise NotImplementedError

    @password.setter
    @abstractmethod
    def password(self, plain_password: str):
        raise NotImplementedError

    @abstractmethod
    def assign_role(self, role_id: int, role_registry: RoleRegistry) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_role(self, role_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_roles(self) -> set[int]:
        raise NotImplementedError
