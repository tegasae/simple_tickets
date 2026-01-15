from dataclasses import dataclass, field
from typing import Optional

import bcrypt

from dataclasses import dataclass, field
from typing import Optional
import bcrypt

from src.domain.admin_empty import AdminEmpty


@dataclass
class Admin:
    id: int
    login: str
    _password_hash: str = field(repr=False)

    def __init__(self, id: int, login: str, password: str):
        self.id = id
        self.login = login
        self._password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, plain_password: str) -> None:
        if not plain_password:
            raise ValueError("Password cannot be empty")
        self._password_hash = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), self._password_hash.encode("utf-8"))


if __name__=="__main__":
#    admin = Admin(id=1, login="test", password="initial")
#    print(admin.password)
#    print(admin.verify_password('initial'))
#    admin.password = "new_password"  # This works!
#    print(admin.password)
#    print(admin.verify_password('new_password'))

    empty_admin=AdminEmpty()
    print(empty_admin.password)