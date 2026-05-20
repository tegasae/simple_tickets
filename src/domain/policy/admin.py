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
        if (not isinstance(admin,Admin) or not isinstance(admin.account, Account) or not admin.enabled
                or not admin.account.enabled):
            raise DomainOperationError("Admin is not valid")