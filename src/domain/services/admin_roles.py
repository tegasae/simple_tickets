from typing import FrozenSet

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.domain.employee import Admin
from src.domain.exceptions import ItemValidationError, DomainOperationError
from src.domain.rbac.admin_rbac import AdminRole
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role import Authorizer, RoleManager

from src.domain.rbac.role_repo_mem import RoleRepo
from src.domain.rbac.role_repository import RoleRepository
from src.domain.repositories.admin_repository import AdminRepository


class AdminRoleService:
    def __init__(self,admin_repository:AdminRepository, role_repository: RoleRepository[AdminPermission]):
        self.admin_repository=admin_repository
        self.role_repository = role_repository
        self.authorizer = Authorizer[AdminPermission](role_repository)
        self.role_manager = RoleManager[AdminPermission](self.authorizer,self.role_repository)

    def grant_role(self,actor_admin_id:int,target_admin_id:int,role_id:int,required_permission:AdminPermission):
        actor_admin=self.admin_repository.get(admin_id=actor_admin_id)
        target_admin = self.admin_repository.get(admin_id=target_admin_id)
        role=self.role_repository.get(role_id=role_id)
        self.role_manager.grant_role(actor=actor_admin,target=target_admin,role_id=role.role_id,required_permission=required_permission)

    def revoke_roles(self,actor_admin_id:int,target_admin_id:int,role_id:int,required_permission:AdminPermission):
        actor_admin=self.admin_repository.get(admin_id=actor_admin_id)
        target_admin = self.admin_repository.get(admin_id=target_admin_id)
        role=self.role_repository.get(role_id=role_id)
        self.role_manager.revoke_role(actor=actor_admin,target=target_admin,role_id=role.role_id,required_permission=required_permission)



    def create_role(self,*,name:str,system_role:bool=False,permissions: FrozenSet[AdminPermission])->AdminRole:
        role=AdminRole(role_id=0,name=name,permissions=permissions,system_role=system_role)
        role=self.role_repository.add(role=role)
        return role

    def delete_role(self,role_id:int):
        if self.role_repository.is_employee_id(role_id=role_id):
            raise DomainOperationError(f"Role id {role_id} has admins")
        self.role_repository.delete(role_id=role_id)


    def add_permission(self):

    def remove_permission(self):


if __name__=='__main__':
    admin_roles_service = AdminRoleService(AdminRepositorySQLite(conn=),RoleRepo())
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



