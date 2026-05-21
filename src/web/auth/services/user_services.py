from src.domain.exceptions import DomainError
from src.domain.policy.user import UserPolicy
from src.services.uow.uow import UnitOfWork
from src.web.auth.exceptions import InvalidCredentialsError
from src.web.auth.models import UserAuth, LoginRequest
from src.web.auth.services.services import AuthServiceAbstract


class UserAuthService(AuthServiceAbstract):


    def __init__(self, uow:UnitOfWork):
        self.uow = uow

    def authenticate_user(
        self,
        login_request:LoginRequest
    ) -> UserAuth:
        """
        Authenticate user credentials.

        Raises:
            InvalidCredentialsError:
                if login/password is wrong.

            UserNotValidError:
                if admin or account exists but is disabled.
        """
        with self.uow:
            try:
                user = self.uow.users.find_by_login(login=login_request.username)
                client = self.uow.clients.get(client_id=user.client_id)
                UserPolicy.ensure_can_login(user=user, client=client, password=login_request.password)
            except DomainError as exc:
                # Do not reveal whether login exists.
                raise InvalidCredentialsError() from exc

            return UserAuth(
                id=user.employee_id,
                username=str(user.account.login),
                scope=self._scope(user),
            )

    def validate_user_exists(
            self,
            login_request: LoginRequest
    ) -> bool:
        """
        Validate that user still exists and is enabled.

        Used during refresh-token flow.
        """
        with self.uow:
            try:
                user = self.uow.users.find_by_login(login=login_request.username)
                client = self.uow.clients.get(client_id=user.client_id)
                UserPolicy.ensure_login_is_still_valid(user=user,client=client)
            except DomainError:
                return False
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
