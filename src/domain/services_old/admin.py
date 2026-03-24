#src/domain/services/admin.py
from src.domain.employee import Admin
from src.domain.account import Account, NoAccount
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.admin_repository import AdminRepository


class AdminService:
    """
    Domain service for Admin use-cases.

    Responsibilities:
        - create admin
        - update admin
        - attach/detach account
        - enable/disable admin
        - delete admin

    Notes:
        - repository handles persistence of account + roles
        - this service only modifies the aggregate
        - application layer should manage transactions
    """

    def __init__(self, admin_repository: AdminRepository):
        self._admin_repository = admin_repository

    # --------------------------------
    # Create
    # --------------------------------

    def create_admin(
        self,
        *,
        job_title: str = "",
        first_name: str,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        login: str | None = None,
        password: str | None = None,
    ) -> Admin:

        admin = Admin.create(
            employee_id=0,
            job_title=job_title,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        if login and password:
            admin.account = Account.create(
                account_id=0,
                login=login,
                plain_password=password,
            )

        admin = self._admin_repository.save(admin)

        return admin

    # --------------------------------
    # Update
    # --------------------------------

    def update_admin(
        self,
        *,
        admin_id: int,
        job_title: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Admin:

        admin = self._admin_repository.get(admin_id)

        admin.update(
            job_title,
            first_name,
            last_name,
            email,
            phone,
        )

        return self._admin_repository.save(admin)

    # --------------------------------
    # Account management
    # --------------------------------

    def attach_account(
        self,
        *,
        admin_id: int,
        login: str,
        password: str,
    ) -> Admin:
        if self._admin_repository.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")

        admin = self._admin_repository.get(admin_id)

        admin.account = Account.create(
            account_id=0,
            login=login,
            plain_password=password,
        )

        return self._admin_repository.save(admin)

    def detach_account(self, *, admin_id: int) -> Admin:

        admin = self._admin_repository.get(admin_id)

        admin.account = NoAccount()

        return self._admin_repository.save(admin)

    def update_password(self, *, admin_id: int, password: str) -> Admin:

        admin = self._admin_repository.get(admin_id)

        if isinstance(admin.account, NoAccount):
            raise DomainOperationError("Admin has no account")

        admin.account = Account.create(
            account_id=admin.account.account_id,
            login=str(admin.account.login),
            plain_password=password,
        )

        return self._admin_repository.save(admin)

    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable_admin(self, *, admin_id: int) -> Admin:

        admin = self._admin_repository.get(admin_id)

        admin.disable()

        if not isinstance(admin.account, NoAccount):
            admin.account.disable()

        return self._admin_repository.save(admin)

    def enable_admin(self, *, admin_id: int) -> Admin:

        admin = self._admin_repository.get(admin_id)

        admin.enable()

        return self._admin_repository.save(admin)

    def disable_admin_account(self, *, admin_id: int) -> Admin:

        admin = self._admin_repository.get(admin_id)

        if isinstance(admin.account, NoAccount):
            raise DomainOperationError("Admin has no account")

        admin.account.disable()

        return self._admin_repository.save(admin)

    def enable_admin_account(self, *, admin_id: int) -> Admin:

        admin = self._admin_repository.get(admin_id)

        if isinstance(admin.account, NoAccount):
            raise DomainOperationError("Admin has no account")

        admin.account.enable()

        return self._admin_repository.save(admin)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        admin_id: int,
        number_of_clients: int,
        number_of_users: int,
        number_of_tickets: int,
    ) -> None:

        if number_of_clients != 0 or number_of_users != 0 or number_of_tickets != 0:
            raise DomainOperationError(
                f"Admin {admin_id} cannot be deleted because dependent entities exist"
            )

        self._admin_repository.delete(admin_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def find_by_login(self, login: str) -> Admin:

        return self._admin_repository.find_by_login(login=login)

    def get_by_id(self, admin_id:int) -> Admin:
        return self._admin_repository.get(admin_id=admin_id)

    def get_all(self) -> list[Admin]:
        return self._admin_repository.get_all()


    # --------------------------------
    # Role operations
    # --------------------------------

    def grant_role(self, *, admin_id: int, role_id: int):

        admin = self._admin_repository.get(admin_id)

        admin.grant_role(role_id)

        admin = self._admin_repository.save(admin)

        return admin

    def revoke_role(self, *, admin_id: int, role_id: int):

        admin = self._admin_repository.get(admin_id)

        admin.revoke_role(role_id)

        admin = self._admin_repository.save(admin)

        return admin

    def get_roles(self, *, admin_id: int) -> frozenset[int]:

        admin = self._admin_repository.get(admin_id)

        return admin.role_ids()