from src.domain.employee import Admin
from src.domain.repositories.admin_repository import AdminRepository
from utils.db.connect import Connection


class AdminRepositorySQLite(AdminRepository):

    def __init__(self, conn: Connection):
        self.conn = conn

        self.saved_version = 0
    def get(self, admin_id: int) -> Admin:
        pass

    def get_all(self) -> list[Admin]:
        pass

    def exists(self, admin_id: int) -> bool:
        pass

    def save(self, admin: Admin) -> Admin:
        pass

    def delete(self, admin_id: int):
        pass

    def find_by_login(self, *, login: str) -> Admin:
        pass

    def exist_login(self, login: str) -> bool:
        pass