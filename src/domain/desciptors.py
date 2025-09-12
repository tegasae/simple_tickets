from dataclasses import dataclass
import bcrypt


@dataclass
class Admin:
    id: int
    login: str
    # store the hash (can also be provided directly); hide from repr
    # password_hash: Optional[str] = field(default=None, repr=False)
    # init-only field for a plain password
    password: str

    # password: str=""

    def __post_init__(self):
        # If plain password was passed, hash it and overwrite/produce password_hash
        # if password is not None:
        #    self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        if self.password is not None:
            self.password = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # If neither provided, error
        if not self.password:
            raise ValueError("Either 'password' (plain) or 'password_hash' must be provided")

    def verify_password(self, plain: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), self.password.encode("utf-8"))


if __name__ == "__main__":
    admin = Admin(id=1, login="login", password="password")
    print(admin.password)
    print(admin.verify_password("password"))
