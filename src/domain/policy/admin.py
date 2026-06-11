from src.domain.account import Account
from src.domain.department import Department
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


    @staticmethod
    def ensure_can_change_department(
                *,
            admin: Admin,
            department: Department | None,
            has_at_work_tickets: bool,
    ) -> None:
            if has_at_work_tickets:
                raise DomainOperationError(
                    "You can't change department because admin has tickets at work"
                )

            if department is not None:
                department.ensure_enabled()
                admin.change_department(department_id=department.department_id)
            else:
                admin.remove_department()