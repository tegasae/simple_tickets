from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Authorizer, RoleManager
from src.services.uow.uow import UnitOfWork


class EmployeeHelper:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def require_actor(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> Admin:
        actor = self.uow.admins.get(admin_id=actor_admin_id)
        Authorizer(self.uow.roles_admin).require(actor, permission)
        return actor

    def get_user(self, *, actor_id:int,user_id: int,permission: AdminPermission) -> (Admin,User):
        actor = self.require_actor(actor_admin_id=actor_id, permission=permission)
        return actor,self.uow.users.get(user_id=user_id)

    def get_admin(self, *, actor_id, admin_id: int,permission: AdminPermission) -> (Admin,Admin):
        actor = self.require_actor(actor_admin_id=actor_id, permission=permission)

        return actor,self.uow.admins.get(admin_id=admin_id)

    def ensure_login_is_free(self,*,login: str | None) -> None:
        if login and self.uow.users.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")


    def get_role_manager_user(self) -> RoleManager:
        authorizer = Authorizer(self.uow.roles_admin)
        return RoleManager(authorizer, self.uow.roles_user)


    def get_role_manager_admin(self) -> RoleManager:
        authorizer = Authorizer(self.uow.roles_admin)
        return RoleManager(authorizer, self.uow.roles_admin)

