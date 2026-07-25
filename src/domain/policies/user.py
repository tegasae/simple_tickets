from src.domain.account import Account
from src.domain.client import Client
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError


class UserPolicy:

    @staticmethod
    def ensure_can_login(user: User, client:Client, password:str) -> None:

        if (not isinstance(user,User) or not isinstance(user.account,Account) or not user.enabled
                or not user.account.enabled or not user.account.verify_password(plain_password=password)
        or not isinstance(client,Client) or not client.enabled):
            raise DomainOperationError("User cannot login")


    @staticmethod
    def ensure_login_is_still_valid(user: User,client:Client) -> None:
        if (not isinstance(user,User) or not isinstance(user.account, Account) or not user.enabled
                or not user.account.enabled or
        not isinstance(client,Client) or not client.enabled):
            raise DomainOperationError("User is not valid")