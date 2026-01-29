from src.adapters.repository import ClientRepository
from src.domain.model import AdminsAggregate


class AdminManagementService:
    """Domain service - knows ONLY about ports/interfaces"""

    def __init__(self,
                 #admin_repository: AdminRepository,  # ← PORT TYPE
                 client_repository: ClientRepository
                 ):
        #self.admin_repo = admin_repository  # ← Accepts ANY implementation
        self.client_repo = client_repository

    def delete_admin(self, admin_id: int,aggregate:AdminsAggregate) -> None:
        # Uses ports, doesn't care about implementations
        clients = self.client_repo.get_client_by_admin_id(admin_id)
        if len(clients) == 0:
            aggregate.remove_admin_by_id(admin_id)