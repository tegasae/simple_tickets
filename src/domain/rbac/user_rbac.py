from src.domain.rbac.permissions import UserPermission
from src.domain.rbac.role import Role, RoleManager, Authorizer, RoleRepo

UserRole = Role[UserPermission]

def build_user_rbac() -> tuple[RoleRepo[UserPermission], Authorizer[UserPermission], RoleManager[UserPermission]]:
    roles = RoleRepo[UserPermission]()
    auth = Authorizer[UserPermission](roles)
    mgr = RoleManager[UserPermission](auth, roles)
    return roles, auth, mgr

