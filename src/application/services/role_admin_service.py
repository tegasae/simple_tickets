from typing import Iterable, Generic
from typing_extensions import TypeVar

from src.domain.exceptions import DomainOperationError
from src.domain.rbac.role_new import Role
from src.domain.rbac.permissions import AdminPermission, UserPermission, PermissionBase
from src.domain.rbac.role_repository import RoleRepository
from src.services.uow.uow import UnitOfWork

# Type variables for different permission types
T = TypeVar("T", bound=PermissionBase)

#todo Добавить проверки на валидлнсть как ticket_service



class RoleService(Generic[T]):
    """
    Generic role services that works with any permission type.

    This services uses the appropriate repository based on permission type.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _get_repository(self, permission_type: type[T]) -> RoleRepository[T]:
        """
        Get the appropriate repository based on permission type.

        This is a type-safe way to select the correct repository.
        """
        if permission_type is AdminPermission:
            return self.uow.roles_admin
        elif permission_type is UserPermission:
            return self.uow.roles_user
        else:
            raise DomainOperationError(f"Unknown permission type: {permission_type}")

    def create_role(
            self,
            *,
            name: str,
            permissions: Iterable[T],
            description: str = "",
            is_system_role: bool = False,
    ) -> Role[T]:
        """
        Create a new role with permissions.

        The permission type is inferred from the permissions iterable.
        """
        # Convert to frozenset and check if we have any permissions
        permissions_set = frozenset(permissions)

        if not permissions_set:
            raise DomainOperationError("Role must have at least one permission")

        # Get the permission type from the first permission
        first_permission = next(iter(permissions_set))
        permission_type = type(first_permission)

        # Verify all permissions are of the same type
        for perm in permissions_set:
            if type(perm) is not permission_type:
                raise DomainOperationError(
                    f"Cannot mix permission types in a single role. "
                    f"Found {permission_type.__name__} and {type(perm).__name__}"
                )

        # Get the appropriate repository
        repo = self._get_repository(permission_type)

        with self.uow:
            role = Role(
                role_id=0,
                name=name,
                permissions=permissions_set,
                description=description,
                is_system_role=is_system_role,
            )
            role = repo.add(role)

        return role

    def delete_role(self, role_id: int, permission_type: type[T]) -> None:
        """
        Delete a role by ID.

        Args:
            role_id: The ID of the role to delete
            permission_type: The permission type to determine which repository to use
        """
        role = self.get_role(role_id, permission_type)

        if role.is_system_role:
            raise DomainOperationError(f"Cannot delete system role: {role.name}")

        repo = self._get_repository(permission_type)

        # Check if role is assigned to any users
        # You might need to add this method to your repository
        if hasattr(repo, 'is_assigned'):
            if repo.is_assigned(role_id=role_id):
                raise DomainOperationError(
                    f"Role '{role.name}' cannot be deleted because it is assigned to users"
                )

        with self.uow:
            repo.delete(role_id)

    def get_role(self, role_id: int, permission_type: type[T]) -> Role[T]:
        """
        Get a role by ID.

        Args:
            role_id: The ID of the role to retrieve
            permission_type: The permission type to determine which repository to use
        """
        repo = self._get_repository(permission_type)
        return repo.get(role_id)

    def get_all_roles(self, permission_type: type[T]) -> Iterable[Role[T]]:
        """
        Get all roles of a specific permission type.

        Args:
            permission_type: The permission type to filter by
        """
        repo = self._get_repository(permission_type)
        return repo.all()


# Specialized services for better type safety

class AdminRoleService:
    """
    Specialized services for admin roles.
    Provides type-safe methods for admin permissions only.
    """

    def __init__(self, uow: UnitOfWork):
        self._service = RoleService[AdminPermission](uow)

    def create_role(
            self,
            *,
            name: str,
            permissions: Iterable[AdminPermission],
            description: str = "",
            is_system_role: bool = False,
    ) -> Role[AdminPermission]:
        """Create an admin role with type-safe permissions."""
        return self._service.create_role(
            name=name,
            permissions=permissions,
            description=description,
            is_system_role=is_system_role,
        )

    def delete_role(self, role_id: int) -> None:
        """Delete an admin role."""
        self._service.delete_role(role_id, AdminPermission)

    def get_role(self, role_id: int) -> Role[AdminPermission]:
        """Get an admin role by ID."""
        return self._service.get_role(role_id, AdminPermission)

    def get_all_roles(self) -> Iterable[Role[AdminPermission]]:
        """Get all admin roles."""
        return self._service.get_all_roles(AdminPermission)


class UserRoleService:
    """
    Specialized services for user roles.
    Provides type-safe methods for user permissions only.
    """

    def __init__(self, uow: UnitOfWork):
        self._service = RoleService[UserPermission](uow)

    def create_role(
            self,
            *,
            name: str,
            permissions: Iterable[UserPermission],
            description: str = "",
            is_system_role: bool = False,
    ) -> Role[UserPermission]:
        """Create a user role with type-safe permissions."""
        return self._service.create_role(
            name=name,
            permissions=permissions,
            description=description,
            is_system_role=is_system_role,
        )

    def delete_role(self, role_id: int) -> None:
        """Delete a user role."""
        self._service.delete_role(role_id, UserPermission)

    def get_role(self, role_id: int) -> Role[UserPermission]:
        """Get a user role by ID."""
        return self._service.get_role(role_id, UserPermission)

    def get_all_roles(self) -> Iterable[Role[UserPermission]]:
        """Get all user roles."""
        return self._service.get_all_roles(UserPermission)


# Optional: Service factory for easy instantiation

class RoleServiceFactory:
    """
    Factory to create appropriate role services.
    This helps with dependency injection and services composition.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def admin_service(self) -> AdminRoleService:
        """Get a services for admin roles."""
        return AdminRoleService(self.uow)

    def user_service(self) -> UserRoleService:
        """Get a services for user roles."""
        return UserRoleService(self.uow)

    def generic_service(self) -> RoleService:
        """Get a generic services for a specific permission type."""
        return RoleService(self.uow)