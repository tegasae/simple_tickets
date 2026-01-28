# services/decorators.py
from functools import wraps
from typing import Callable
from src.domain.permissions.rbac import Permission


def requires_permission_id(permission: Permission):
    """Decorator to check admin permissions before executing method"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, requesting_admin_id: int, *args, **kwargs):
            # 1. Get fresh aggregate


            # 2. Check permission

            #requesting_admin=self.uow.admins.get_by_id(requesting_admin_id)
            requesting_admin = self.uow.admins.get_by_id(self.admin_requesting_id)
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


def with_aggregate_transaction(func: Callable):
    """Decorator to handle the repetitive UoW pattern"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if already in transaction (nested calls)
        if hasattr(self, '_current_aggregate'):
            # Already in transaction, reuse aggregate
            return func(self, self._current_aggregate, *args, **kwargs)

        # Start new transaction
        with self.uow:
            aggregate = self._get_fresh_aggregate()
            # Store aggregate for nested calls
            self._current_aggregate = aggregate

            try:
                result = func(self, aggregate, *args, **kwargs)
                self.uow.admins.save_admins(aggregate)
                self.uow.commit()
                return result
            finally:
                # Clean up
                delattr(self, '_current_aggregate')

    return wrapper


