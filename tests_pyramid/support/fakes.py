from __future__ import annotations

from collections.abc import Iterator
from dataclasses import is_dataclass, replace
from typing import Any, Generic, TypeVar

from src.domain.rbac.role_new import Role

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(
        self,
        id_attr: str,
        items: list[T] | None = None,
        *,
        calls: list[str] | None = None,
        save_label: str = "save",
        delete_label: str = "delete",
    ) -> None:
        self.id_attr = id_attr
        self.items: dict[int, T] = {}
        self.next_id = 1
        self.calls = calls
        self.save_label = save_label
        self.delete_label = delete_label

        for item in items or []:
            item_id = int(getattr(item, id_attr))
            self.items[item_id] = item
            if item_id >= self.next_id:
                self.next_id = item_id + 1

    def save(self, entity: T | None = None, **kwargs: T) -> T:
        if entity is None:
            entity = next(iter(kwargs.values()), None)
        if entity is None:
            raise TypeError("save() requires entity")

        if self.calls is not None:
            self.calls.append(self.save_label)

        entity_id = int(getattr(entity, self.id_attr))
        if entity_id == 0:
            entity_id = self.next_id
            self.next_id += 1
            try:
                setattr(entity, self.id_attr, entity_id)
            except (AttributeError, TypeError):
                if not is_dataclass(entity):
                    raise
                entity = replace(entity, **{self.id_attr: entity_id})

        self.items[entity_id] = entity
        return entity

    # RoleRepository compatibility.
    add = save

    def get(self, entity_id: int | None = None, **kwargs: int) -> T:
        if entity_id is None:
            for key in (
                self.id_attr,
                "admin_id",
                "user_id",
                "employee_id",
                "client_id",
                "ticket_id",
                "department_id",
                "role_id",
            ):
                value = kwargs.get(key)
                if value is not None:
                    entity_id = value
                    break

        if entity_id is None or int(entity_id) <= 0:
            raise KeyError(entity_id)

        return self.items[int(entity_id)]

    def get_all(self) -> list[T]:
        return list(self.items.values())

    def all(self) -> list[T]:
        return self.get_all()

    def delete(self, entity_id: int | None = None, **kwargs: int) -> None:
        if entity_id is None:
            entity_id = next(iter(kwargs.values()))
        if self.calls is not None:
            self.calls.append(self.delete_label)
        del self.items[int(entity_id)]

    def exists(self, entity_id: int) -> bool:
        return int(entity_id) in self.items

    def exist_login(self, login: str) -> bool:
        for entity in self.items.values():
            account = getattr(entity, "account", None)
            entity_login = getattr(account, "login", "")
            if str(entity_login) == login:
                return True
        return False

    def exist_email(self, email: str) -> bool:
        return any(str(getattr(entity, "email", "")) == email for entity in self.items.values())

    def find_by_login(self, *, login: str) -> T:
        for entity in self.items.values():
            account = getattr(entity, "account", None)
            if str(getattr(account, "login", "")) == login:
                return entity
        raise KeyError(login)

    def get_all_by_client_id(self, *, client_id: int) -> list[T]:
        return [
            entity
            for entity in self.items.values()
            if getattr(entity, "client_id", None) == client_id
        ]

    def get_all_by_department_id(self, *, department_id: int) -> list[T]:
        return [
            entity
            for entity in self.items.values()
            if getattr(entity, "department_id", None) == department_id
        ]

    def iter_get_all(self, *, batch_size: int = 500) -> Iterator[T]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        yield from self.items.values()

    def iter_by_client_id(self, *, client_id: int, batch_size: int = 500) -> Iterator[T]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        for entity in self.items.values():
            if getattr(entity, "client_id", None) == client_id:
                yield entity

    def does_client_exist(self, client_id: int) -> bool:
        return any(getattr(entity, "client_id", None) == client_id for entity in self.items.values())

    def does_user_exist(self, user_id: int) -> bool:
        return any(
            getattr(entity, "user_id", None) == user_id
            or getattr(entity, "contact_user_id", None) == user_id
            for entity in self.items.values()
        )

    def has_department_reference(self, department_id: int) -> bool:
        return any(getattr(entity, "department_id", None) == department_id for entity in self.items.values())

    def has_created_by_admin(self, *, admin_id: int) -> bool:
        return any(getattr(entity, "created_by_admin_id", None) == admin_id for entity in self.items.values())

    def has_admin_reference(self, admin_id: int) -> bool:
        for entity in self.items.values():
            if hasattr(entity, "belong") and entity.belong(admin_id):
                return True
        return False

    def get_by_user_ticket_id(self, user_ticket_id: int) -> T:
        for entity in self.items.values():
            if getattr(entity, "user_ticket_id", 0) == user_ticket_id:
                return entity
        raise KeyError(user_ticket_id)


class InMemoryRoleRepository(InMemoryRepository[Role[Any]]):
    def __init__(
        self,
        items: list[Role[Any]] | None = None,
        *,
        calls: list[str] | None = None,
    ) -> None:
        super().__init__("role_id", items, calls=calls, save_label="save_role", delete_label="delete_role")
        self.assigned_role_ids: set[int] = set()

    def is_assigned(self, *, role_id: int) -> bool:
        return role_id in self.assigned_role_ids


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.admins = InMemoryRepository("employee_id", calls=self.calls, save_label="save_admin")
        self.users = InMemoryRepository("employee_id", calls=self.calls, save_label="save_user")
        self.clients = InMemoryRepository("client_id", calls=self.calls, save_label="save_client")
        self.departments = InMemoryRepository("department_id", calls=self.calls, save_label="save_department")
        self.tickets = InMemoryRepository("ticket_id", calls=self.calls, save_label="save_ticket")
        self.user_tickets = InMemoryRepository("ticket_id", calls=self.calls, save_label="save_ticket_user")
        self.roles_admin = InMemoryRoleRepository(calls=self.calls)
        self.roles_user = InMemoryRoleRepository(calls=self.calls)
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.calls.append("enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.calls.append("exit")
        if exc_type is not None:
            self.rollback()
        return False

    def commit(self) -> None:
        self.calls.append("commit")
        self.committed = True

    def rollback(self) -> None:
        self.calls.append("rollback")
        self.rolled_back = True
