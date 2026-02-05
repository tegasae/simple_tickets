from src.domain.rbac_new.core import Role, AdminPermission, RoleRepo, Authorizer, RoleManager

AdminRole = Role[AdminPermission]
def build_admin_rbac() -> tuple[RoleRepo[AdminPermission], Authorizer[AdminPermission], RoleManager[AdminPermission]]:
    roles = RoleRepo[AdminPermission]()
    auth = Authorizer[AdminPermission](roles)
    mgr = RoleManager[AdminPermission](auth, roles)
    return roles, auth, mgr