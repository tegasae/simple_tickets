# services/decorators.py
from functools import wraps
from typing import Callable, Any
from src.domain.permissions.rbac import Permission


def requires_permission(permission: Permission):
    """Decorator to check admin permissions before executing method"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, requesting_admin_id: int, *args, **kwargs):
            # 1. Get fresh aggregate
            aggregate = self._get_fresh_aggregate()

            # 2. Check permission
            requesting_admin = aggregate.get_admin_by_id(requesting_admin_id)
            self.admin_roles_management_service.check_permission(
                admin=requesting_admin,
                permission=permission
            )

            # 3. Execute with transaction
            #with self.uow:
            result = func(self, requesting_admin_id, *args, **kwargs)
            #    self.uow.admins.save_admins(aggregate)
            #    self.uow.commit()
            return result

        return wrapper

    return decorator