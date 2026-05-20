from src.domain.exceptions import DomainError
from src.domain.policy.admin import AdminPolicy
from src.services.uow.uow import UnitOfWork
from src.web.auth.exceptions import InvalidCredentialsError
from src.web.auth.models import UserAuth
from src.web.auth.services.services import AuthServiceAbstract


class AdminAuthService(AuthServiceAbstract):
    """
    Authentication service for Admin realm.

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
        username: str,
        password: str,
    ) -> UserAuth:
        """
        Authenticate admin credentials.

        Raises:
            InvalidCredentialsError:
                if login/password is wrong.

            UserNotValidError:
                if admin or account exists but is disabled.
        """
        with self.uow:
            try:
                admin = self.uow.admins.find_by_login(login=username)
                AdminPolicy.ensure_can_login(admin, password)
            except DomainError as exc:
                # Do not reveal whether login exists.
                raise InvalidCredentialsError() from exc

            return UserAuth(
                id=admin.employee_id,
                username=str(admin.account.login),
                scope=self._scope(admin),
            )

    def validate_user_exists(
            self,
            username: str,
    ) -> bool:
        """
        Validate that admin still exists and is enabled.

        Used during refresh-token flow.
        """
        with self.uow:
            try:
                admin = self.uow.admins.find_by_login(login=username)
                AdminPolicy.ensure_login_is_still_valid(admin=admin)
            except DomainError:
                return False
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
