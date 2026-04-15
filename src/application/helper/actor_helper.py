from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role import Authorizer
from src.services.uow.uow import UnitOfWork


class EmployeeActorHelper:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> Admin:
        actor = self.uow.admins.get(admin_id=actor_admin_id)
        Authorizer(self.uow.roles_admin).require(actor, permission)
        return actor


    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> User:
        actor = self.uow.users.get(user_id=actor_user_id)
        Authorizer(self.uow.roles_admin).require(actor, permission)
        return actor
