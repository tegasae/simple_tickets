# commands/admin_commands.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.domain.model import AdminsAggregate, Admin
from src.domain.services.admins import AdminManagementService


@dataclass
class AdminCommand(ABC):
    """Base command for admin operations"""
    requesting_admin_id: int
    target_admin_id: int

    @abstractmethod
    def execute(self, aggregate: AdminsAggregate) -> Any:
        pass


@dataclass
class ChangeAdminEmailCommand(AdminCommand):
    new_email: str

    def execute(self, aggregate: AdminsAggregate) -> Admin:
        return aggregate.change_admin_email(self.target_admin_id, self.new_email)


@dataclass
class DeleteAdminCommand(AdminCommand):
    management_service: AdminManagementService

    def execute(self, aggregate: AdminsAggregate) -> None:
        self.management_service.delete_admin(self.target_admin_id, aggregate)


# Updated AdminService
class AdminService(BaseService[Admin]):



    @requires_permission_id(Permission.UPDATE_ADMIN)
    def update_admin_email(self, requesting_admin_id: int,
                           target_admin_id: int, new_email: str) -> Admin:
        command = ChangeAdminEmailCommand(
            requesting_admin_id=requesting_admin_id,
            target_admin_id=target_admin_id,
            new_email=new_email
        )
        return self._execute_command(command)

    @requires_permission_id(Permission.DELETE_ADMIN)
    def remove_admin_by_id(self, requesting_admin_id: int,
                           target_admin_id: int) -> None:
        if requesting_admin_id == target_admin_id:
            raise DomainOperationError("Admin cannot delete themselves")

        command = DeleteAdminCommand(
            requesting_admin_id=requesting_admin_id,
            target_admin_id=target_admin_id,
            management_service=self.management_service
        )
        self._execute_command(command)