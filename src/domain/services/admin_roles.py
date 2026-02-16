from src.domain.employee import Admin
from src.domain.rbac.admin_rbac import AdminRole
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Authorizer, RoleManager

from src.domain.rbac.role_repo_mem import RoleRepo
from src.domain.rbac.role_repository import RoleRepository
from src.domain.services.admin import AdminService


class AdminRoleService:
    def __init__(self,role_repo: RoleRepository[AdminPermission]):
        self.role_repo = role_repo
        self.authorizer = Authorizer[AdminPermission](role_repo)
        self.role_manager = RoleManager[AdminPermission](self.authorizer,self.role_repo)




if __name__=='__main__':
    admin_roles_service = AdminRoleService(RoleRepo())
    role_manager=admin_roles_service.role_manager
    admin1=Admin.create(employee_id=1,job_title="1",first_name="John",last_name="Doe",email="r@tt.tt",phone="")
    admin2 = Admin.create(employee_id=2, job_title="1", first_name="John1", last_name="Doe1", email="r@tt.tt", phone="")
    role_repo_memory = admin_roles_service.role_repo

    role_repo_memory.add(
        AdminRole(
            role_id=1,
            name="SuperAdmin",
            permissions=frozenset({
                AdminPermission.VIEW_ADMIN,
                AdminPermission.UPDATE_ADMIN,
                AdminPermission.ASSIGN_ROLE,
                AdminPermission.REVOKE_ROLE,
                AdminPermission.VIEW_AUDIT_LOG,
            }),
            is_system_role=True,
        )
    )

    role_repo_memory.add(
        AdminRole(
            role_id=2,
            name="Admin",
            permissions=frozenset({
                AdminPermission.VIEW_ADMIN,
                AdminPermission.VIEW_AUDIT_LOG,
            }),
            is_system_role=True,
        )
    )

    admin1.grant_role(1)
    print(admin2.role_ids())
    role_manager.grant_role(actor=admin1,target=admin2,role_id=1,required_permission= AdminPermission.VIEW_ADMIN)
    print(admin2.role_ids())



