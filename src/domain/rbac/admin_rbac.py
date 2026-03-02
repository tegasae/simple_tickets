from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import RoleManager, Authorizer
from src.domain.rbac.role_new import Role
from src.domain.rbac.role_repo_mem import RoleRepoMem
from src.domain.rbac.role_repository import RoleRepository

AdminRole = Role[AdminPermission]
def build_admin_rbac() -> tuple[RoleRepository[AdminPermission], Authorizer[AdminPermission], RoleManager[AdminPermission]]:
    roles = RoleRepoMem()
    auth = Authorizer[AdminPermission](roles)
    mgr = RoleManager[AdminPermission](auth, roles)
    return roles, auth, mgr