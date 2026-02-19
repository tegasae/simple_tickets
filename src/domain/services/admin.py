# src/domain/services/admin_service.py


from src.domain.employee import Admin
from src.domain.account import NoAccount
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.repositories.admin_repository import AdminRepository
from src.domain.services.employee_account import EmployeeAccountService


# ---------------------------
# Services
# ---------------------------

# -------- Account attach/detach --------


class AdminService:
    """
    Admin use-cases:
      - create admin (without account)
      - soft delete / hard delete
      - attach/detach account (optional)
      - enable/disable account (only if attached)

    Notes:
      - No transaction management here (UoW can wrap later).
      - Authorization/RBAC checks should happen in application layer
        or in a dedicated auth/role service.
    """

    def __init__(
        self,
        admin_repository: AdminRepository,
        account_repository: AccountRepository,


    ):
        self._admin_repository = admin_repository
        self._account_repository = account_repository
        self._account_service = EmployeeAccountService(account_repository=account_repository)


    # -------- Create / delete admin --------

    def create_admin(
        self,
        *,
        admin_id: int,
        job_title: str = "",
        first_name: str,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        login: str | None = None,
        password: str | None = None
    ) -> Admin:
        admin = Admin.create(
            employee_id=admin_id,
            job_title=job_title,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        admin=self._admin_repository.save(admin)
        if login and password:
            account=self._account_service.attach_account(employee_id=admin.employee_id, login=login, plain_password=password)
            admin.account = account
        else:
            admin.account=NoAccount()
        return admin

    def update_admin(self,*,admin_id:int,job_title: str |None,first_name: str | None = None, last_name: str | None = None, email: str | None = None,phone: str | None = None)->Admin:
        admin = self._admin_repository.get(admin_id)
        admin.update(job_title,first_name, last_name, email, phone)
        admin=self._admin_repository.save(admin)
        return admin


    def update_admin_password(self,*,admin_id: int,password: str):
        admin = self._admin_repository.get(admin_id)
        self._account_service.update_password(employee_id=admin.employee_id, password=password)


    def disable_admin(self, *, admin_id: int):
        admin = self._admin_repository.get(admin_id)
        admin.disable()
        self._account_service.disable_account(employee_id=admin.employee_id)

        admin=self._admin_repository.save(admin)
        return admin

    def enable_admin(self, *, admin_id: int):
        admin = self._admin_repository.get(admin_id)
        admin.enable()
        admin = self._admin_repository.save(admin)
        return admin

    def delete(self, *, admin_id: int, number_of_client:int, number_of_users:int,number_of_tickets) -> None:
        """
        Hard delete is rare. Optionally also delete the attached account.
        """
        # Ensure admin exists
        #####
        #check if admin has created clients, tickets and other
        #####
        if number_of_tickets!= 0 or number_of_users!= 0 or number_of_client != 0:
            raise DomainOperationError(f"Admin id {admin_id} cannot be deleted because has other elements")
        self._account_service.detach_account(employee_id=admin_id)
        self._admin_repository.delete(admin_id=admin_id)







