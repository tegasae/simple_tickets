from abc import ABC, abstractmethod
from typing import List

from src.domain.model import AdminsAggregate, AdminAbstract, Admin, AdminEmpty


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
    def _get_admin_by_id(self, admin_id)->AdminAbstract:
        raise NotImplementedError()

    @abstractmethod
    def _add_admin(self, admin):
        raise NotImplementedError()

    @abstractmethod
    def _get_admin_by_name(self, name)->AdminAbstract:
        raise NotImplementedError()

    @abstractmethod
    def _update_admin(self, admin):
        raise NotImplementedError()

    @abstractmethod
    def _remove_admin(self, name):
        raise NotImplementedError()

    @abstractmethod
    def _get_list_of_admins(self)->AdminsAggregate:
        raise NotImplementedError()

    @abstractmethod
    def _save_admins(self, aggregate):
        raise NotImplementedError()




class InMemoryAdminRepository(AdminRepositoryAbstract):
    """In-memory implementation of Admin repository"""

    def __init__(self):
        self._aggregate = AdminsAggregate()  # Empty initial aggregate
        self._version = 0
        self._empty_admin = AdminEmpty()

    def _get_list_of_admins(self) -> AdminsAggregate:
        """Return the current in-memory aggregate"""
        return self._aggregate

    def _save_admins(self, aggregate: AdminsAggregate) -> None:
        """Replace the in-memory aggregate with the new one"""
        self._aggregate = aggregate
        self._version += 1

    def _get_admin_by_id(self, admin_id: int) -> AdminAbstract:
        """Get admin by ID from the in-memory aggregate"""
        aggregate = self._get_list_of_admins()
        for admin in aggregate.admins.values():
            if hasattr(admin, 'admin_id') and admin.admin_id == admin_id:
                return admin
        return self._empty_admin

    def _get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by name from the in-memory aggregate"""
        aggregate = self._get_list_of_admins()
        return aggregate.admins.get(name, self._empty_admin)

    def _add_admin(self, admin: Admin) -> None:
        """Add admin to the in-memory aggregate"""
        aggregate = self._get_list_of_admins()

        # Check for duplicates
        if admin.name in aggregate.admins:
            raise ValueError(f"Admin with name '{admin.name}' already exists")

        if any(a.admin_id == admin.admin_id for a in aggregate.admins.values()):
            raise ValueError(f"Admin with ID {admin.admin_id} already exists")

        # Add to aggregate
        aggregate.admins[admin.name] = admin
        aggregate.version += 1

        # Save the updated aggregate
        self._save_admins(aggregate)

    def _update_admin(self, admin: Admin) -> None:
        """Update admin in the in-memory aggregate"""
        aggregate = self._get_list_of_admins()

        if admin.name not in aggregate.admins:
            raise ValueError(f"Admin '{admin.name}' not found")

        # Update the admin reference
        aggregate.admins[admin.name] = admin
        aggregate.version += 1

        # Save the updated aggregate
        self._save_admins(aggregate)

    def _remove_admin(self, name: str) -> None:
        """Remove admin from the in-memory aggregate"""
        aggregate = self._get_list_of_admins()

        if name not in aggregate.admins:
            raise ValueError(f"Admin '{name}' not found")

        # Remove from aggregate
        del aggregate.admins[name]
        aggregate.version += 1

        # Save the updated aggregate
        self._save_admins(aggregate)

    # Additional helper methods
    def get_version(self) -> int:
        """Get current version of the repository"""
        return self._version

    def clear(self) -> None:
        """Clear all admins from the repository"""
        self._aggregate = AdminsAggregate()
        self._version += 1

    def load_initial_data(self, admins: List[Admin]) -> None:
        """Load initial set of admins"""
        aggregate = AdminsAggregate()
        for admin in admins:
            aggregate.admins[admin.name] = admin
        self._save_admins(aggregate)


# Usage examples
if __name__ == "__main__":
    # Create repository
    repo = InMemoryAdminRepository()

    # Create some admins
    admin1 = Admin(1, "john_doe", "password123", "john@example.com", True)
    admin2 = Admin(2, "jane_smith", "password456", "jane@example.com", False)

    # Add admins to repository
    repo.add_admin(admin1)
    repo.add_admin(admin2)

    # Get the aggregate
    aggregate1 = repo.get_list_of_admins()
    print(f"Total admins: {len(aggregate1.admins)}")
    print(f"Repository version: {repo.get_version()}")

    # Get individual admins
    john = repo.get_admin_by_name("john_doe")
    jane = repo.get_admin_by_id(2)
    nonexistent = repo.get_admin_by_name("nonexistent")

    print(f"Found John: {not john.is_empty() if hasattr(john, 'is_empty') else 'Unknown'}")
    print(f"Found Jane: {not jane.is_empty() if hasattr(jane, 'is_empty') else 'Unknown'}")
    print(f"Found nonexistent: {not nonexistent.is_empty() if hasattr(nonexistent, 'is_empty') else 'Unknown'}")

    # Update an admin
    if hasattr(john, 'email'):
        john.email = "john.new@example.com"
        repo.update_admin(john)
        print(f"Updated John's email, new version: {repo.get_version()}")

    # Remove an admin
    repo.remove_admin("jane_smith")
    print(f"Removed Jane, new version: {repo.get_version()}")
    print(f"Remaining admins: {len(repo.get_list_of_admins().admins)}")