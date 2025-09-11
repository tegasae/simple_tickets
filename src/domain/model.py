from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
import re
from hashlib import sha256


@dataclass
class Admin:
    id: int
    name: str  # UNIQUE constraint
    email: str
    password_hash: str
    enabled: bool
    date_created: datetime = field(default_factory=datetime.now)

    def __eq__(self, other):
        # Use name for equality since name must be unique
        return isinstance(other, Admin) and self.name == other.name

    def __hash__(self):
        return hash(self.name)  # Hash based on unique name

    @classmethod
    def create(cls, admin_id: int, name: str, email: str, password: str, enabled: bool = True) -> 'Admin':
        """Factory method with validation"""
        if not name or not name.strip():
            raise ValueError("Admin name cannot be empty")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        return cls(
            id=admin_id,
            name=name.strip(),
            email=email,
            password_hash=cls.hash_password(password),
            enabled=enabled
        )

    @staticmethod
    def hash_password(password: str) -> str:
        return sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self.password_hash == self.hash_password(password)


class AdminsAggregate:
    def __init__(self, admins: List[Admin] = None, version: int = 0):
        self.admins: Dict[str, Admin] = {}  # Name as key ensures uniqueness
        self.version = version
        if admins:
            for admin in admins:
                self.add_admin(admin)  # Use add_admin to enforce uniqueness

    def add_admin(self, admin: Admin):
        if admin.name in self.admins:
            raise ValueError(f"Admin with name '{admin.name}' already exists")

        # Additional check if ID also needs to be unique
        if any(a.id == admin.id for a in self.admins.values()):
            raise ValueError(f"Admin with ID {admin.id} already exists")

        self.admins[admin.name] = admin
        self.version += 1

    def get_admin_by_name(self, name: str) -> Admin:
        """Get admin by unique name"""
        return self.admins.get(name)

    def admin_exists(self, name: str) -> bool:
        """Check if admin with given name exists"""
        return name in self.admins

    def change_admin_email(self, name: str, new_email: str):
        """Change email for specific admin"""
        admin = self.get_admin_by_name(name)
        if not admin:
            raise ValueError(f"Admin '{name}' not found")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            raise ValueError("Invalid email format")

        admin.email = new_email
        self.version += 1

    def change_admin_password(self, name: str, new_password: str):
        """Change password for specific admin"""
        admin = self.get_admin_by_name(name)
        if not admin:
            raise ValueError(f"Admin '{name}' not found")

        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")

        admin.password_hash = Admin.hash_password(new_password)
        self.version += 1

    def toggle_admin_status(self, name: str, enabled: bool = None):
        """Enable/disable admin or toggle status"""
        admin = self.get_admin_by_name(name)
        if not admin:
            raise ValueError(f"Admin '{name}' not found")

        if enabled is None:
            admin.enabled = not admin.enabled  # Toggle
        else:
            admin.enabled = enabled

        self.version += 1

    def remove_admin(self, name: str):
        if name not in self.admins:
            raise ValueError(f"Admin '{name}' not found")

        del self.admins[name]
        self.version += 1

    def get_all_admins(self) -> List[Admin]:
        return list(self.admins.values())

    def get_enabled_admins(self) -> List[Admin]:
        return [admin for admin in self.admins.values() if admin.enabled]

    def get_disabled_admins(self) -> List[Admin]:
        return [admin for admin in self.admins.values() if not admin.enabled]