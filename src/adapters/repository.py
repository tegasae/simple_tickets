from abc import ABC, abstractmethod

from src.domain.model import AdminsAggregate, AdminAbstract, Admin


class AdminRepositoryAbstract(ABC):
    """Abstract repository that works with AdminsAggregate"""

    def get_list_of_admins(self) -> AdminsAggregate:
        """Load the entire aggregate from persistence"""
        return self._get_list_of_admins()

    def save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        self._save_admins(aggregate)

    def get_admin_by_id(self, admin_id: int) -> AdminAbstract:
        """Get individual admin by ID"""
        return self._get_admin_by_id(admin_id)

    def get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get individual admin by name"""
        return self._get_admin_by_name(name)

    def add_admin(self, admin: Admin) -> None:
        """Add a new admin"""
        self._add_admin(admin)

    def update_admin(self, admin: Admin) -> None:
        """Update an existing admin"""
        self._update_admin(admin)

    def remove_admin(self, name: str) -> None:
        """Remove admin by name"""
        self._remove_admin(name)

    @abstractmethod
    def _get_admin_by_id(self, admin_id) -> AdminAbstract:
        raise NotImplementedError()

    @abstractmethod
    def _add_admin(self, admin):
        raise NotImplementedError()

    @abstractmethod
    def _get_admin_by_name(self, name) -> AdminAbstract:
        raise NotImplementedError()

    @abstractmethod
    def _update_admin(self, admin):
        raise NotImplementedError()

    @abstractmethod
    def _remove_admin(self, name):
        raise NotImplementedError()

    @abstractmethod
    def _get_list_of_admins(self) -> AdminsAggregate:
        raise NotImplementedError()

    @abstractmethod
    def _save_admins(self, aggregate):
        raise NotImplementedError()
