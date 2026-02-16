# src/domain/services/admin_service.py


from src.domain.employee import Admin
from src.domain.account import Account, NoAccount
from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.repositories.employee_repository import AdminRepository



# ---------------------------
# Services
# ---------------------------

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

    ) -> None:
        self._admin_repository = admin_repository


    # -------- Create / delete admin --------

    def create_admin(
        self,
        *,
        admin_id: int,
        job_title: str = "",
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
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
        return admin

    def update_admin(self,*,admin_id:int,job_title: str |None,first_name: str | None = None, last_name: str | None = None, email: str | None = None,phone: str | None = None)->Admin:
        admin = self._admin_repository.get(admin_id)
        admin.update(job_title,first_name, last_name, email, phone)
        admin=self._admin_repository.save(admin)
        return admin



    def disable_admin(self, *, admin_id: int)-> Admin:
        admin = self._admin_repository.get(admin_id)
        admin.disable()
        admin.account.disable()
        admin=self._admin_repository.save(admin)
        return admin

    def enable_admin(self, *, admin_id: int)-> Admin:
        admin = self._admin_repository.get(admin_id)
        admin.enable()
        admin.account.enable()
        admin = self._admin_repository.save(admin)
        return admin

    def delete(self, *, admin_id: int, number_of_clients:int, number_of_users:int,number_of_tickets) -> None:
        """
        Hard delete is rare. Optionally also delete the attached account.
        """
        # Ensure admin exists
        #####
        #check if admin has created clients, tickets and other
        #####
        if number_of_tickets!= 0 or number_of_users!= 0 or number_of_tickets != 0:
            raise DomainOperationError(f"Admin id {admin_id} cannot be deleted because has other elements")
        self._admin_repository.delete(admin_id=admin_id)


    # -------- Account attach/detach --------

    def attach_account(
        self,
        *,
        admin_id: int,
        login: str,
        plain_password: str,
    ) -> int:
        """
        Create a new Account and attach it to an Admin.

        Raises:
          - DomainOperationError if admin already has an account
          - ItemValidationError if login already exists
        """
        admin = self._admin_repository.get(admin_id)


        if isinstance(admin.account, Account):
            raise DomainOperationError(f"Admin {admin_id} already has an account")

        if self._admin_repository.exist_login(login=login):
            raise ItemValidationError(f"Login '{login}' is already taken")

        account = Account.create(account_id=0,login=login, plain_password=plain_password)
        admin.account=account
        admin.version+=1
        admin=self._admin_repository.save(admin)
        return admin.account.account_id

    def detach_account(self, *, admin_id: int) -> None:
        """
        Detach account from admin (does NOT delete account).
        """
        admin=self._admin_repository.get(admin_id)  # ensure exists
        admin.version+=1
        admin.account=NoAccount()
        self._admin_repository.save(admin)

    # -------- Account enable/disable (only if attached) --------

    def disable_account(self, *, admin_id: int) -> None:
        admin = self._admin_repository.get(admin_id)
        admin.account.disable()
        admin.version+=1
        self._admin_repository.save(admin)

    def enable_account(self, *, admin_id: int) -> None:
        admin=self._admin_repository.get(admin_id)
        admin.account.enable()
        admin.version += 1
        self._admin_repository.save(admin)


    def update_password(self, *, admin_id: int, password:str) -> None:
        admin=self._admin_repository.get(admin_id)

        if isinstance(admin.account, Account):
            admin.account.change_password(plain_password=password)
            admin.version+=1
        self._admin_repository.save(admin)


    def check_password(self, *, admin_id: int, password: str) -> bool:
        admin=self._admin_repository.get(admin_id=admin_id)
        return admin.account.verify_password(plain_password=password)

    def find_by_login(self, *, login: str) -> Admin:
        admin=self._admin_repository.find_by_login(login=login)
        return admin





