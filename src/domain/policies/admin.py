from src.domain.account import Account

from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError


class AdminPolicy:

    @staticmethod
    def ensure_can_login(admin: Admin, password:str) -> None:
        if (not isinstance(admin,Admin) or not isinstance(admin.account,Account) or not admin.enabled
                or not admin.account.enabled or not admin.account.verify_password(plain_password=password)):
            raise DomainOperationError("Admin cannot login")


    @staticmethod
    def ensure_login_is_still_valid(admin: Admin) -> None:
        if not isinstance(admin, Admin):
            raise DomainOperationError("Admin is not valid")
        AdminPolicy.ensure_login_state_is_valid(
            admin_enabled=admin.enabled,
            account_enabled=isinstance(admin.account, Account) and admin.account.enabled,
        )

    @staticmethod
    def ensure_login_state_is_valid(*, admin_enabled: bool, account_enabled: bool) -> None:
        if not admin_enabled or not account_enabled:
            raise DomainOperationError("Admin is not valid")


