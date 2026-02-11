from src.domain.rbac.permissions import UserPermission
from src.domain.rbac.role import RoleManager, Authorizer
from src.domain.rbac.role_new import Role
from src.domain.rbac.role_repo_mem import RoleRepo
from src.domain.repositories.role_repository import RoleRepository

UserRole = Role[UserPermission]

def build_user_rbac() -> tuple[RoleRepository[UserPermission], Authorizer[UserPermission], RoleManager[UserPermission]]:
    roles = RoleRepo()
    auth = Authorizer[UserPermission](roles)
    mgr = RoleManager[UserPermission](auth, roles)
    return roles, auth, mgr

