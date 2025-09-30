from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Final, Optional
from abc import ABC, abstractmethod
import re
import bcrypt

# Constants
EMPTY_ADMIN_ID: Final[int] = 0
MIN_PASSWORD_LENGTH: Final[int] = 8
EMAIL_REGEX: Final[str] = r"[^@]+@[^@]+\.[^@]+"


class AdminAbstract(ABC):
    """Abstract base class for all Admin types"""

    @property
    @abstractmethod
    def admin_id(self) -> int:
        raise NotImplementedError

    @admin_id.setter
    @abstractmethod
    def admin_id(self, value: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @name.setter
    @abstractmethod
    def name(self, value: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def email(self) -> str:
        raise NotImplementedError

    @email.setter
    @abstractmethod
    def email(self, value: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool):
        raise NotImplementedError

    @property
    @abstractmethod
    def date_created(self) -> datetime:
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __bool__(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def verify_password(self, password: str) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def password(self):
        raise NotImplementedError

    @password.setter
    @abstractmethod
    def password(self, plain_password: str):
        raise NotImplementedError


@dataclass
class Admin(AdminAbstract):
    _admin_id: int
    _name: str
    _email: str
    _password_hash: str = field(repr=False)
    _enabled: bool
    _date_created: datetime = field(default_factory=datetime.now)

    def __init__(self, admin_id: int, name: str, password: str, email: str, enabled: bool,
                 date_created: Optional[datetime] = None):
        self._admin_id = admin_id
        self._name = name
        self._email = email
        self._enabled = enabled
        self._password_hash = Admin.str_hash(password)
        self._date_created = date_created or datetime.now()
        # Property implementations with setters

    @property
    def admin_id(self) -> int:
        return self._admin_id

    @admin_id.setter
    def admin_id(self, value: int):
        self._admin_id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        self._email = value

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def date_created(self) -> datetime:
        return self._date_created

    def __eq__(self, other) -> bool:
        if isinstance(other, AdminEmpty):
            return False
        return isinstance(other, Admin) and self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __bool__(self) -> bool:
        return True

    def is_empty(self) -> bool:
        return False

    @property
    def password(self):
        # raise AttributeError("Password is write-only - use verify_password() to check passwords")
        return self._password_hash

    @password.setter
    def password(self, plain_password: str) -> None:
        if not plain_password:
            raise ValueError("Password cannot be empty")
        self._password_hash = Admin.str_hash(plain_password)

    @staticmethod
    def str_hash(s: str) -> str:
        return bcrypt.hashpw(s.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def str_verify(plain_str: str, hash_str: str) -> bool:
        return bcrypt.checkpw(plain_str.encode("utf-8"), hash_str.encode("utf-8"))

    def verify_password(self, password: str) -> bool:
        return self.str_verify(password, self._password_hash)


@dataclass
class AdminEmpty(AdminAbstract):
    """Null Object implementation of AdminAbstract"""
    _admin_id: int = EMPTY_ADMIN_ID
    _name: str = ""
    _email: str = ""
    _enabled: bool = False
    _date_created: datetime = field(default_factory=datetime.now)

    # Property implementations with setters that raise errors
    @property
    def admin_id(self) -> int:
        return self._admin_id

    @admin_id.setter
    def admin_id(self, value: int):
        raise AttributeError("Cannot set admin_id on empty admin")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        raise AttributeError("Cannot set name on empty admin")

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        raise AttributeError("Cannot set email on empty admin")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        raise AttributeError("Cannot set enabled on empty admin")

    @property
    def date_created(self) -> datetime:
        return self._date_created

    def __eq__(self, other) -> bool:
        return isinstance(other, AdminEmpty)

    def __bool__(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return True

    def verify_password(self, password: str) -> bool:
        return False

    @property
    def password(self):
        raise AttributeError("Cannot access password on empty admin")


    @password.setter
    def password(self, plain_password: str):
        raise AttributeError("Cannot set password on empty admin")

    def __getattr__(self, name):
        """Catch any other method calls and raise appropriate error"""
        raise AttributeError(f"Cannot call '{name}' on empty admin")


class AdminsAggregate:
    def __init__(self, admins: List[Admin] = None, version: int = 0):
        self.admins: Dict[str, AdminAbstract] = {}
        self.version: int = version
        self._empty_admin = AdminEmpty()

        if admins:
            for admin in admins:
                self.add_admin(admin)

    # Reusable validation methods
    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate and sanitize admin name"""
        if not name or not name.strip():
            raise ValueError("Admin name cannot be empty")
        return name.strip()

    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email format"""
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format")
        return email

    @staticmethod
    def _validate_password(password: str) -> str:
        """Validate password strength"""
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        return password

    def _validate_admin_id_unique(self, admin_id: int):
        """Validate that admin ID is unique"""
        if any(a.admin_id == admin_id for a in self.admins.values() if not a.is_empty()):
            raise ValueError(f"Admin with ID {admin_id} already exists")

    def _validate_admin_name_unique(self, name: str):
        """Validate that admin name is unique"""
        if name in self.admins:
            raise ValueError(f"Admin with name '{name}' already exists")

    def create_admin(self, admin_id: int, name: str, email: str, password: str, enabled: bool = True) -> Admin:
        """Create a new admin with validation"""
        validated_name = AdminsAggregate._validate_name(name)
        validated_email = AdminsAggregate._validate_email(email)
        validated_password = AdminsAggregate._validate_password(password)
        self._validate_admin_id_unique(admin_id)
        self._validate_admin_name_unique(validated_name)

        admin = Admin(
            admin_id=admin_id,
            name=validated_name,
            password=validated_password,
            email=validated_email,
            enabled=enabled
        )
        self.add_admin(admin)
        return admin

    def add_admin(self, admin: AdminAbstract):
        """Add an existing admin with validation"""
        #todo При добавлении созданого admin не валидируется имя, email, пароль.
        # Это связано с порнографией добавления уже хешированного пароля

        if isinstance(admin, Admin):
            # self._validate_admin_id_unique(admin.admin_id)
            self._validate_admin_name_unique(admin.name)

            self.admins[admin.name] = admin
            self.version += 1

    def change_admin(self, admin: AdminAbstract):
        """Change an existing admin with validation"""
        # todo При изменении admin не валидируется имя, email, пароль.
        #  Это связано с порнографией добавления уже хешированного пароля
        if isinstance(admin, Admin):
            if admin.name in self.admins and self.admins[admin.name].admin_id == admin.admin_id:
                self.admins[admin.name] = admin
                self.version += 1

    def get_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by unique name - returns AdminEmpty if not found"""
        return self.admins.get(name, self._empty_admin)

    def require_admin_by_name(self, name: str) -> AdminAbstract:
        """Get admin by name - throws exception if not found"""
        admin = self.admins.get(name)
        if not admin or admin.is_empty():
            raise ValueError(f"Admin '{name}' not found")
        return admin

    def admin_exists(self, name: str) -> bool:
        """Check if admin with given name exists"""
        return name in self.admins and not self.admins[name].is_empty()

    def change_admin_email(self, name: str, new_email: str):
        """Change email for specific admin"""
        admin = self.require_admin_by_name(name)
        validated_email = AdminsAggregate._validate_email(new_email)

        admin.email = validated_email
        self.version += 1

    def change_admin_password(self, name: str, new_password: str):
        """Change password for specific admin"""
        admin = self.require_admin_by_name(name)
        validated_password = AdminsAggregate._validate_password(new_password)

        admin.password = validated_password
        self.version += 1

    def toggle_admin_status(self, name: str):
        """Toggle admin status (enable ↔ disable)"""
        admin = self.require_admin_by_name(name)
        admin.enabled = not admin.enabled
        self.version += 1

    def set_admin_status(self, name: str, enabled: bool):
        """Set specific admin status"""
        admin = self.require_admin_by_name(name)
        admin.enabled = enabled
        self.version += 1

    def remove_admin(self, name: str):
        """Remove admin by name"""
        if name not in self.admins:
            raise ValueError(f"Admin '{name}' not found")
        del self.admins[name]
        self.version += 1

    def get_all_admins(self) -> List[AdminAbstract]:
        """Get all real admins (exclude empty ones)"""
        return [admin for admin in self.admins.values() if not admin.is_empty()]

    def get_enabled_admins(self) -> List[AdminAbstract]:
        return [admin for admin in self.get_all_admins() if admin.enabled]

    def get_disabled_admins(self) -> List[AdminAbstract]:
        return [admin for admin in self.get_all_admins() if not admin.enabled]

    def get_admin_count(self) -> int:
        return len(self.get_all_admins())

    def is_empty(self) -> bool:
        return self.get_admin_count() == 0


# Test the fix
if __name__ == "__main__":
    aggregate = AdminsAggregate()

    # Create a real admin
    admin1 = aggregate.create_admin(1, "test", "test@example.com", "password123", True)
    print(admin1.password)
    # Test property setters
    real_admin = aggregate.require_admin_by_name("test")
    print(f"Original email: {real_admin.email}")

    # This will work now!
    real_admin.email = "new.email@example.com"
    print(f"Updated email: {real_admin.email}")

    # Test with empty admin (will raise error)
    empty_admin = aggregate.get_admin_by_name("nonexistent")
    try:
        empty_admin.email = "test@example.com"  # This will raise AttributeError
    except AttributeError as e:
        print(f"Expected error for empty admin: {e}")
