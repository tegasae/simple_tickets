#src/role_registry.py
from src.domain.exceptions import ItemNotFoundError
from src.domain.permissions.role import UserRole, EmptyUserRole


class NewRoleRegistry:
    """Registry for User roles only"""

    def __init__(self, list_roles: list[UserRole]=None):
        self._roles_by_id: dict[int, UserRole] = {}
        self._roles_by_name: dict[str, UserRole] = {}
        self._load_default_roles([EmptyUserRole()])
        if list_roles:
            self._load_default_roles(list_roles)

    def _load_default_roles(self, list_roles: list[UserRole]):
        """Load the two default user roles"""
        #ordinary_role = OrdinaryUserRole()
        #super_role = SuperUserRole()
        for role in list_roles:
            self._roles_by_id[role.role_id] = role
            self._roles_by_name[role.name] = role



    def get_role_by_id(self, role_id: int) -> UserRole:
        """Get role by ID, returns EmptyUserRole if not found"""
        return self._roles_by_id.get(role_id, EmptyUserRole())

    def get_role_by_name(self, name: str) -> UserRole:
        """Get role by name, returns EmptyUserRole if not found"""
        return self._roles_by_name.get(name, EmptyUserRole())

    def role_exists_by_id(self, role_id: int) -> bool:
        return role_id in self._roles_by_id

    def role_exists_by_name(self, name: str) -> bool:
        return name in self._roles_by_name

    def require_role_by_id(self, role_id: int) -> UserRole:
        """Get role or raise exception"""
        role = self.get_role_by_id(role_id)
        if isinstance(role, EmptyUserRole):
            raise ItemNotFoundError(f"User role ID {role_id} not found")
        return role

    def get_all_roles(self) -> list[UserRole]:
        """Get all registered user roles"""
        return list(self._roles_by_id.values())
