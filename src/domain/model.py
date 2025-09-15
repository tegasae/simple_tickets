from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Final
import re

import bcrypt

# Constants
EMPTY_ADMIN_ID: Final[int] = 0
MIN_PASSWORD_LENGTH: Final[int] = 8



@dataclass
class Admin:
    admin_id: int
    name: str  # UNIQUE constraint
    email: str
    _password_hash: str = field(repr=False)
    enabled: bool
    date_created: datetime = field(default_factory=datetime.now)

    def __init__(self, admin_id: int, name: str, password: str, email: str, enabled: bool):
        self.admin_id = admin_id
        self.name = name
        self.email = email
        self.enabled = enabled
        self._password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.date_created = datetime.now()

    def __eq__(self, other):
        # Use name for equality since name must be unique
        return isinstance(other, Admin) and self.name == other.name

    def __hash__(self):
        return hash(self.name)  # Hash based on unique name

    # def __post_init__(self):
    #    if not self.password:
    #        raise ValueError("Either 'password must be provided")
    #    self.password = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @property
    def password(self):
        raise AttributeError("Password is write-only - use verify_password() to check passwords")

    @password.setter
    def password(self, plain_password: str) -> None:
        if not plain_password:
            raise ValueError("Password cannot be empty")
        self._password_hash = Admin.str_hash(plain_password)

    @staticmethod
    def str_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def str_verify(plain_str: str, hash_str: str):
        return bcrypt.checkpw(plain_str.encode("utf-8"), hash_str.encode("utf-8"))

    def verify_password(self, password: str) -> bool:
        return self.str_verify(password, self._password_hash)

@dataclass
class AdminEmpty(Admin):
    """Null object for Admin - follows the same interface but does nothing"""
    admin_id: int = 0
    name: str = ""
    email: str = ""
    enabled: bool = False
    date_created: datetime = datetime.now()
    _password_hash: str = ""

    def __eq__(self, other):
        return isinstance(other, AdminEmpty)

    def verify_password(self, password: str) -> bool:
        return False

    @property
    def password(self):
        raise AttributeError("Cannot access password on empty admin")

    @password.setter
    def password(self, plain_password: str):
        raise AttributeError("Cannot set password on empty admin")

    def __bool__(self):
        return False


class AdminsAggregate:
    def __init__(self, admins: List[Admin] = None, version: int = 0):
        self.admins: Dict[str, Admin] = {}  # Name as key ensures uniqueness
        self.version = version
        if admins:
            for admin in admins:
                self.add_admin(admin)  # Use add_admin to enforce uniqueness

    def create_admin(self, admin_id: int, name: str, email: str, password: str, enabled: bool = True) -> Admin:

        if not name or not name.strip():
            raise ValueError("Admin name cannot be empty")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        admin = Admin(
            admin_id=admin_id,
            name=name.strip(),
            email=email,
            password=password,
            enabled=enabled
        )
        self.add_admin(admin)
        return admin

    def add_admin(self, admin: Admin):
        if admin.name in self.admins:
            raise ValueError(f"Admin with name '{admin.name}' already exists")

        # Additional check if ID also needs to be unique
        if any(a.admin_id == admin.admin_id for a in self.admins.values()):
            raise ValueError(f"Admin with ID {admin.admin_id} already exists")

        self.admins[admin.name] = admin
        self.version += 1

    def get_admin_by_name(self, name: str) -> Admin:
        """Get admin by unique name"""
        return self.admins.get(name,AdminEmpty())

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

        ########
        admin.password = new_password
        ##########
        self.version += 1

    def toggle_admin_status(self, name: str):
        """Toggle admin status (enable ↔ disable)"""
        admin = self.get_admin_by_name(name)
        admin.enabled = not admin.enabled
        self.version += 1

    def set_admin_status(self, name: str, enabled: bool):
        """Set specific admin status"""
        admin = self.get_admin_by_name(name)
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

if __name__=="__main__":
    admin_empty=AdminEmpty()
    print(admin_empty._password_hash)