from src.domain.employee import User
from src.domain.account import Account, NoAccount
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.user_repository import UserRepository


class UserService:
    """
    Domain service for User use-cases.

    Responsibilities:
        - create user
        - update user
        - attach/detach account
        - enable/disable user
        - delete user

    Notes:
        - repository handles persistence of account + roles
        - this service only modifies the aggregate
        - application layer should manage transactions
    """

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    # --------------------------------
    # Create
    # --------------------------------

    def create_user(
        self,
        *,
        client_id: int,
        first_name: str,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        login: str | None = None,
        password: str | None = None,
    ) -> User:

        user = User.create(
            employee_id=0,
            client_id=client_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        if login and password:
            user.account = Account.create(
                account_id=0,
                login=login,
                plain_password=password,
            )

        user = self._user_repository.save(user)

        return user

    # --------------------------------
    # Update
    # --------------------------------

    def update_user(
        self,
        *,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:

        user = self._user_repository.get(user_id)

        user.update(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        return self._user_repository.save(user)

    # --------------------------------
    # Account management
    # --------------------------------

    def attach_account(
        self,
        *,
        user_id: int,
        login: str,
        password: str,
    ) -> User:
        if self._user_repository.exist_login(login):
            raise DomainOperationError(f"Login {login} already exists")
        user = self._user_repository.get(user_id)

        user.account = Account.create(
            account_id=0,
            login=login,
            plain_password=password,
        )

        return self._user_repository.save(user)

    def detach_account(self, *, user_id: int) -> User:

        user = self._user_repository.get(user_id)

        user.account = NoAccount()

        return self._user_repository.save(user)

    def update_password(self, *, user_id: int, password: str) -> User:

        user = self._user_repository.get(user_id)

        if isinstance(user.account, NoAccount):
            raise DomainOperationError("User has no account")

        user.account = Account.create(
            account_id=user.account.account_id,
            login=str(user.account.login),
            plain_password=password,
        )

        return self._user_repository.save(user)

    # --------------------------------
    # Enable / disable
    # --------------------------------

    def disable_user(self, *, user_id: int) -> User:

        user = self._user_repository.get(user_id)

        user.disable()

        if not isinstance(user.account, NoAccount):
            user.account.disable()

        return self._user_repository.save(user)

    def enable_user(self, *, user_id: int) -> User:

        user = self._user_repository.get(user_id)

        user.enable()

        return self._user_repository.save(user)

    def disable_user_account(self, *, user_id: int) -> User:

        user = self._user_repository.get(user_id)

        if isinstance(user.account, NoAccount):
            raise DomainOperationError("User has no account")

        user.account.disable()

        return self._user_repository.save(user)

    def enable_user_account(self, *, user_id: int) -> User:

        user = self._user_repository.get(user_id)

        if isinstance(user.account, NoAccount):
            raise DomainOperationError("User has no account")

        user.account.enable()

        return self._user_repository.save(user)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        user_id: int,
        number_of_tickets: int,
        number_of_user_tickets: int,
    ) -> None:

        if number_of_tickets != 0 or number_of_user_tickets != 0:
            raise DomainOperationError(
                f"User {user_id} cannot be deleted because dependent entities exist"
            )

        self._user_repository.delete(user_id)

    # --------------------------------
    # Queries
    # --------------------------------

    def find_by_login(self, login: str) -> User:

        return self._user_repository.find_by_login(login=login)

    def get_by_id(self, user_id: int) -> User:
        return self._user_repository.get(user_id=user_id)

    def get_all(self) -> list[User]:
        return self._user_repository.get_all()

    # --------------------------------
    # Role operations
    # --------------------------------

    def grant_role(self, *, user_id: int, role_id: int):

        user = self._user_repository.get(user_id)

        user.grant_role(role_id)

        user = self._user_repository.save(user)

        return user

    def revoke_role(self, *, user_id: int, role_id: int):

        user = self._user_repository.get(user_id)

        user.revoke_role(role_id)

        user = self._user_repository.save(user)

        return user

    def get_roles(self, *, user_id: int) -> frozenset[int]:

        user = self._user_repository.get(user_id)

        return user.role_ids()

