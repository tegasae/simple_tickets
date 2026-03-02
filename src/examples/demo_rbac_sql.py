import sqlite3

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.domain.employee import Admin
from src.domain.rbac.admin_rbac import AdminRole
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_repo_mem import RoleRepoMem
from src.domain.services.admin_roles import AdminRoleService
from utils.db.connect import Connection

if __name__=='__main__':
    conn1 = Connection.create_connection(url="../../db/admins.db", engine=sqlite3)
    admin_roles_service = AdminRoleService(AdminRepositorySQLite(conn=conn1),RoleRepoMem())
    role_manager=admin_roles_service.role_manager
    admin1=Admin.create(employee_id=1,job_title="1",first_name="John",last_name="Doe",email="r@tt.tt",phone="")
    admin2 = Admin.create(employee_id=2, job_title="1", first_name="John1", last_name="Doe1", email="r@tt.tt", phone="")
    role_repo_memory = admin_roles_service.role_repository

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



