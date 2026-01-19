import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime

import re
from typing import Final, Optional


from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError, ItemValidationError, DomainOperationError
from src.domain.permissions.rbac import Permission, RoleRegistry

# Constants
EMPTY_ADMIN_ID: Final[int] = 0
MIN_PASSWORD_LENGTH: Final[int] = 8
EMAIL_REGEX: Final[str] = r"[^@]+@[^@]+\.[^@]+"





@dataclass
class Admin:
    """Пользователи владельцев системы. Обладают полными правами в системе."""
    """name используется как login. Возможно, в дальнейшем добавить дополнительную информацию о пользователе и ввести
    отдельном поле login"""
    """пароль храниться в хэшированном виде"""
    """Дата создания не меняется"""
    """Обращения к полям только через свойства"""
    _admin_id: int
    _name: str
    _email: str
    _password_hash: str = field(repr=False)
    _enabled: bool
    _date_created: datetime = field(default_factory=datetime.now)
    _roles_ids: set[int] = field(default_factory=set)  # ← Store IDs, not names!
    def __init__(self, admin_id: int, name: str, password: str, email: str, enabled: bool,
                 roles_ids: Optional[set[int]] = None,
                 date_created: Optional[datetime] = None,created_clients=0):

        self._admin_id = admin_id
        self._name = name
        self._email = email
        self._enabled = enabled
        self._roles_ids = roles_ids or set()
        self._password_hash = Admin.str_hash(password)
        self._date_created = date_created or datetime.now()
        self.created_clients = created_clients


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

        # New RBAC methods

    def has_role(self, role_id: int) -> bool:
        return role_id in self._roles_ids


    def has_permission(self, permission: Permission, role_registry: RoleRegistry) -> bool:
        """Check if admin has permission through any of their roles"""
        if not self._enabled:
            return False

        for role_id in self._roles_ids:  # ← Iterate through IDs
            role = role_registry.get_role_by_id(role_id)  # ← Look up by ID
            if role and role.has_permission(permission):
                return True
        return False

    def assign_role(self, role_id: int, role_registry: RoleRegistry) -> None:
        """Assign a role to admin"""
        role = role_registry.require_role_by_id(role_id)
        self._roles_ids.add(role.role_id)

    def remove_role(self, role_id: int) -> None:
        """Remove a role from admin"""
        self._roles_ids.discard(role_id)

    def get_roles(self) -> set[int]:
        return set(self._roles_ids)  # Return copy


    def __eq__(self, other) -> bool:
        """Если этот экземпляр это AdminEmpty, то они не равны"""
        if isinstance(other, Admin) and other.is_empty():
            return False
        """Админы равны по именам"""
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

        """Hash password with SHA-256 and random salt"""
        # Generate a cryptographically secure random salt
        salt = secrets.token_bytes(32)

        # Hash the password with the salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + s.encode('utf-8'))
        hashed_password = hash_obj.hexdigest()

        # Return salt + hash in a format that can be stored
        # Encode salt as hex for storage
        salt_hex = salt.hex()
        return f"{salt_hex}:{hashed_password}"

    @staticmethod
    def str_verify(plain_str: str, hash_str: str) -> bool:
        #return bcrypt.checkpw(plain_str.encode("utf-8"), hash_str.encode("utf-8"))
        """Verify password against stored hash"""
        try:
            # Split the stored hash into salt and hash
            salt_hex, original_hash = hash_str.split(':')

            # Convert hex salt back to bytes
            salt = bytes.fromhex(salt_hex)

            # Hash the provided password with the same salt
            hash_obj = hashlib.sha256()
            hash_obj.update(salt + plain_str.encode('utf-8'))
            computed_hash = hash_obj.hexdigest()

            # Compare the computed hash with the stored hash
            return secrets.compare_digest(computed_hash, original_hash)

        except (ValueError, AttributeError):
            return False

    def verify_password(self, password: str) -> bool:
        return self.str_verify(password, self._password_hash)


class AdminsAggregate:
    def __init__(self, admins: list[Admin] = None, version: int = 0):
        self.admins: dict[str, Admin] = {}
        self.version: int = version
        #self._empty_admin = AdminEmpty()

        if admins:
            for admin in admins:
                self.add_admin(admin)

    # Reusable validation methods
    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate and sanitize admin name"""
        if not name or not name.strip():
            raise ItemValidationError(message=f"Admin name cannot be empty")
        return name.strip()

    @staticmethod
    def _validate_email(email: str) -> str:
        """Validate email format"""
        if not re.match(EMAIL_REGEX, email):
            raise ItemValidationError(message=f"Invalid email format {email}")
        return email

    @staticmethod
    def _validate_password(password: str) -> str:
        """Validate password strength"""
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ItemValidationError(message=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        return password

    def _validate_admin_id_unique(self, admin_id: int):
        """Validate that admin ID is unique"""
        if any(a.admin_id == admin_id for a in self.admins.values() if not a.is_empty()):
            raise ItemAlreadyExistsError(str(admin_id))

    def _validate_admin_name_unique(self, name: str):
        """Validate that admin name is unique"""
        if name in self.admins:
            raise ItemAlreadyExistsError(name)

    def create_admin(self, admin_id: int, name: str, email: str, password: str, enabled: bool = True,roles:set[int]=()) -> Admin:
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
            enabled=enabled,
            roles_ids=roles
        )
        self.version+=1
        self.add_admin(admin)
        return admin

    def add_admin(self, admin: Admin):
        """Add an existing admin with validation"""
        # todo При добавлении созданного admin не валидируется имя, email, пароль.
        # Это связано с порнографией добавления уже хэшированного пароля

        if isinstance(admin, Admin):
            # self._validate_admin_id_unique(admin.admin_id)
            self._validate_admin_name_unique(admin.name)

            self.admins[admin.name] = admin
            #self.version += 1

    def change_admin(self, admin: Admin):
        """Change an existing admin with validation"""
        # todo При изменении admin не валидируется имя, email, пароль.
        #  Это связано с порнографией добавления уже хэшированного пароля
        if isinstance(admin, Admin):
            if admin.name in self.admins and self.admins[admin.name].admin_id == admin.admin_id:
                self.admins[admin.name] = admin
                self.version += 1

    def get_admin_by_name(self, name: str) -> Admin:
        admin=self.admins.get(name)
        if not admin:
            raise ItemNotFoundError(f"Admin {name} not found")
        return admin

    def require_admin_by_name(self, name: str) -> Admin:
        """Get admin by name - throws exception if not found"""
        admin = self.admins.get(name)
        if not isinstance(admin,Admin) or admin.is_empty():
            raise ItemNotFoundError(name)
        return admin

    def admin_exists(self, name: str) -> bool:
        """Check if admin with given name exists"""
        return name in self.admins and not self.admins[name].is_empty()

    def change_admin_email(self, admin_id: int, new_email: str)->Admin:
        """Change email for specific admin"""
        admin = self.get_admin_by_id(admin_id=admin_id)
        validated_email = AdminsAggregate._validate_email(new_email)
        admin.email = validated_email
        self.version += 1
        return admin

    def change_admin_password(self, admin_id: int, new_password: str)->Admin:
        """Change password for specific admin"""
        admin = self.get_admin_by_id(admin_id)
        validated_password = AdminsAggregate._validate_password(new_password)

        admin.password = validated_password
        self.version += 1
        return admin

    def toggle_admin_status(self, admin_id: int)->Admin:
        """Toggle admin status (enable ↔ disable)"""
        admin = self.get_admin_by_id(admin_id=admin_id)
        admin.enabled = not admin.enabled
        self.version += 1
        return admin

    def set_admin_status(self, admin_id: int, enabled: bool)->Admin:
        """Set specific admin status"""
        admin = self.get_admin_by_id(admin_id)
        admin.enabled = enabled
        self.version += 1
        return admin

    def remove_admin_by_id(self, admin_id: int):
        """Remove admin by id"""
        for name in self.admins:
            if self.admins[name].admin_id == admin_id:
                if self.admins[name].created_clients!=0:
                    raise DomainOperationError(
                        f"Cannot delete admin '{self.admins[name].name}'. It has {self.admins[name].created_clients}."
                    )
                self.version += 1
                del (self.admins[name])
                return
        raise ItemNotFoundError(f"Admin {admin_id} not found")

    def get_all_admins(self) -> list[Admin]:
        """Get all real admins (exclude empty ones)"""
        return [admin for admin in self.admins.values() if not admin.is_empty() and isinstance(admin,Admin)]

    def get_admin_by_id(self, admin_id: int) -> Admin:
        for name in self.admins:
            if self.admins[name].admin_id == admin_id:
                admin=self.admins[name]
                if isinstance(admin,Admin):
                    return admin
        raise ItemNotFoundError(f"Admin {admin_id} not found")

    def get_enabled_admins(self) -> list[Admin]:
        return [admin for admin in self.get_all_admins() if admin.enabled]

    def get_disabled_admins(self) -> list[Admin]:
        return [admin for admin in self.get_all_admins() if not admin.enabled]

    def get_admin_count(self) -> int:
        return len(self.get_all_admins())

    def is_empty(self) -> bool:
        return self.get_admin_count() == 0

