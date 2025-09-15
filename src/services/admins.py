from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import AdminAbstract, Admin


class AdminService:
    """Application service that coordinates between aggregate and repository"""

    def __init__(self, repository: AdminRepositoryAbstract):
        self._repo = repository

    def create_admin(self, admin_id: int, name: str, email: str, password: str, enabled: bool = True) -> Admin:
        aggregate = self._repo.get_aggregate()
        admin = aggregate.create_admin(admin_id, name, email, password, enabled)
        self._repo.save_aggregate(aggregate)
        return admin

    def change_admin_email(self, name: str, new_email: str):
        aggregate = self._repo.get_aggregate()
        aggregate.change_admin_email(name, new_email)
        self._repo.save_aggregate(aggregate)

    def change_admin_password(self, name: str, new_password: str):
        aggregate = self._repo.get_aggregate()
        aggregate.change_admin_password(name, new_password)
        self._repo.save_aggregate(aggregate)

    def toggle_admin_status(self, name: str):
        aggregate = self._repo.get_aggregate()
        aggregate.toggle_admin_status(name)
        self._repo.save_aggregate(aggregate)

    def remove_admin(self, name: str):
        aggregate = self._repo.get_aggregate()
        aggregate.remove_admin(name)
        self._repo.save_aggregate(aggregate)

    def get_admin_by_name(self, name: str) -> AdminAbstract:
        aggregate = self._repo.get_aggregate()
        return aggregate.get_admin_by_name(name)

    # ... other service methods that delegate to aggregate ...
