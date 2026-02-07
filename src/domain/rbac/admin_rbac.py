from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Role, RoleManager, Authorizer, RoleRepo

AdminRole = Role[AdminPermission]
def build_admin_rbac() -> tuple[RoleRepo[AdminPermission], Authorizer[AdminPermission], RoleManager[AdminPermission]]:
    roles = RoleRepo[AdminPermission]()
    auth = Authorizer[AdminPermission](roles)
    mgr = RoleManager[AdminPermission](auth, roles)
    return roles, auth, mgr