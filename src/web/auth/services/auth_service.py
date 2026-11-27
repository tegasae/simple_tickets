from abc import abstractmethod, ABC

from src.domain.exceptions import DomainError
from src.domain.policies.admin import AdminPolicy
from src.domain.policies.user import UserPolicy
from src.domain.uow.unit_of_work import UnitOfWork

from src.web.auth.exceptions import InvalidCredentialsError
from src.web.auth.models import LoginRequest, UserAuth


class AuthServiceAbstract(ABC):
    """
    Abstraction for concrete Admin/User authentication.

    Concrete implementations:
        - AdminAuthService
        - UserAuthService

    They should:
        - check login/password;
        - check enabled flags;
        - return UserAuth.
    """

    @abstractmethod
    def authenticate_user(
        self,
        login_request: LoginRequest,
        *,
        for_session: bool = False,
    ) -> UserAuth:
        raise NotImplementedError

    @abstractmethod
    def validate_user_exists(
        self,
        login_request: LoginRequest,
        *,
        expected_subject_id: int | None = None,
        expected_account_id: int | None = None,
        for_session: bool = False,
    ) -> bool:
        raise NotImplementedError


class AdminAuthService(AuthServiceAbstract):
    """
    Authentication services for Admin realm.

    Responsibilities:
        - find admin by login/name;
        - check that admin exists;
        - check that admin is enabled;
        - check that admin account is enabled;
        - verify password;
        - return UserAuth for token issuing.

    Does NOT:
        - create JWT;
        - create refresh token;
        - know subject_type;
        - know FastAPI;
        - know HTTP.
    """

    def __init__(self, uow:UnitOfWork):
        self.uow = uow

    def authenticate_user(
        self,
        login_request: LoginRequest,
        *,
        for_session: bool = False,
    ) -> UserAuth:
        """
        Authenticate admin credentials.

        Raises:
            InvalidCredentialsError:
                if login/password is wrong.

            UserNotValidError:
                if admin or account exists but is disabled.
        """
        with self.uow.transaction(join=for_session):
            try:
                admin = self.uow.admins.find_by_login(login=login_request.username)
                AdminPolicy.ensure_can_login(admin, login_request.password)
            except DomainError as exc:
                # Do not reveal whether login exists.
                raise InvalidCredentialsError() from exc

            if for_session:
                self.uow.admins.touch(admin)
            return UserAuth(
                id=admin.employee_id,
                account_id=admin.account.account_id,
                username=str(admin.account.login),
                scope=self._scope(admin),
            )

    def validate_user_exists(
            self,
            login_request: LoginRequest,
            *,
            expected_subject_id: int | None = None,
            expected_account_id: int | None = None,
            for_session: bool = False,
    ) -> bool:
        """
        Validate that admin still exists and is enabled.

        Used during refresh-token flow.
        """
        with self.uow.transaction(join=for_session):
            try:
                admin = self.uow.admins.find_by_login(login=login_request.username)
                if expected_subject_id is not None and admin.employee_id != expected_subject_id:
                    return False
                AdminPolicy.ensure_login_is_still_valid(admin=admin)
                if expected_account_id is not None and admin.account.account_id != expected_account_id:
                    return False
            except DomainError:
                return False
            if for_session:
                self.uow.admins.touch(admin)
        return True


    @staticmethod
    def _scope(admin) -> list[str]:
        """
        Convert admin permissions/roles to token scopes.

        For now this can return an empty list if you do not use OAuth scopes yet.

        Later you can map permissions to strings, for example:
            ticket.create
            ticket.update
            client.create
            user.disable
        """

        return []



class UserAuthService(AuthServiceAbstract):


    def __init__(self, uow:UnitOfWork):
        self.uow = uow

    def authenticate_user(
        self,
        login_request: LoginRequest,
        *,
        for_session: bool = False,
    ) -> UserAuth:
        """
        Authenticate user credentials.

        Raises:
            InvalidCredentialsError:
                if login/password is wrong.

            UserNotValidError:
                if admin or account exists but is disabled.
        """
        with self.uow.transaction(join=for_session):
            try:
                user = self.uow.users.find_by_login(login=login_request.username)
                client = self.uow.clients.get(client_id=user.client_id)
                UserPolicy.ensure_can_login(user=user, client=client, password=login_request.password)
            except DomainError as exc:
                # Do not reveal whether login exists.
                raise InvalidCredentialsError() from exc

            if for_session:
                self.uow.users.touch(user)
            return UserAuth(
                id=user.employee_id,
                account_id=user.account.account_id,
                username=str(user.account.login),
                scope=self._scope(user),
            )

    def validate_user_exists(
            self,
            login_request: LoginRequest,
            *,
            expected_subject_id: int | None = None,
            expected_account_id: int | None = None,
            for_session: bool = False,
    ) -> bool:
        """
        Validate that user still exists and is enabled.

        Used during refresh-token flow.
        """
        with self.uow.transaction(join=for_session):
            try:
                user = self.uow.users.find_by_login(login=login_request.username)
                if expected_subject_id is not None and user.employee_id != expected_subject_id:
                    return False
                client = self.uow.clients.get(client_id=user.client_id)
                UserPolicy.ensure_login_is_still_valid(user=user,client=client)
                if expected_account_id is not None and user.account.account_id != expected_account_id:
                    return False
            except DomainError:
                return False
            if for_session:
                self.uow.users.touch(user)
        return True


    @staticmethod
    def _scope(user) -> list[str]:
        """
        Convert admin permissions/roles to token scopes.

        For now this can return an empty list if you do not use OAuth scopes yet.

        Later you can map permissions to strings, for example:
            ticket.create
            ticket.update
            client.create
            user.disable
        """

        return []
