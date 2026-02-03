from __future__ import annotations

import binascii
from dataclasses import dataclass
import base64
import hashlib
import hmac
import os
import re
from typing import Optional


_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*d)(?=.*[^ws]).+$"
)
# Требования:
# - минимум 8 символов
# - хотя бы одна строчная, одна заглавная, одна цифра, один спецсимвол


def _validate_password(password: str, min_len: int = 8) -> None:
    if len(password) < min_len:
        raise ValueError(f"Password must be at least {min_len} characters long")
    if not _PASSWORD_RE.match(password):
        raise ValueError(
            "Password must contain lowercase, uppercase, digit, and special character"
        )


def _pbkdf2_hash_password(
    password: str,
    *,
    iterations: int = 210_000,
    salt: Optional[bytes] = None,
) -> str:
    if salt is None:
        salt = os.urandom(16)

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${salt_b64}${dk_b64}"


def _pbkdf2_verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_str, salt_b64, dk_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_str)

        def _b64decode_nopad(s: str) -> bytes:
            pad = "=" * (-len(s) % 4)
            return base64.urlsafe_b64decode(s + pad)

        salt = _b64decode_nopad(salt_b64)
        expected = _b64decode_nopad(dk_b64)
    except (ValueError, binascii.Error):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


@dataclass(slots=True)
class Account:
    login: str
    password_hash: str  # В БД хранится только хэш, не сырой пароль.

    @classmethod
    def create(cls, login: str, password: str) -> "Account":
        """Создание нового аккаунта: валидирует пароль и хэширует."""
        _validate_password(password)
        return cls(login=login, password_hash=_pbkdf2_hash_password(password))

    @classmethod
    def from_db(cls, login: str, password_hash: str) -> "Account":
        """Загрузка из БД: пароль НЕ хэшируем повторно."""
        return cls(login=login, password_hash=password_hash)

    def set_password(self, new_password: str) -> None:
        """Смена пароля: валидирует и перезаписывает хэш."""
        _validate_password(new_password)
        self.password_hash = _pbkdf2_hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля при логине."""
        return _pbkdf2_verify_password(password, self.password_hash)
