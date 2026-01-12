from src.domain.tickets import Ticket


class TicketManagementService:
    """Domain Service enforcing cross-aggregate rules"""

    def __init__(
                self,
                admins_aggregate,  # Your existing AdminsAggregate
                clients_aggregate,  # Your existing ClientsAggregate
                tickets_aggregate  # New TicketsAggregate
        ):
            self.admins = admins_aggregate
            self.clients = clients_aggregate
            self.tickets = tickets_aggregate

    def create_ticket(
                self,
                admin_name: str,
                client_name: str,
                text: str,
                executor: str = "",
                comment: str = ""
        ) -> Ticket:
            """
            Business rule 4: Ticket can be created only by enabled Admin for enabled Client
            """
            # Check admin exists and enabled
            admin = self.admins.require_admin_by_name(admin_name)
            if admin.is_empty() or not admin.enabled:
                raise ValueError(f"Admin '{admin_name}' not enabled or doesn't exist")

            # Check client exists and enabled
            client = self.clients.get_client_by_name(client_name)
            if client.is_empty or not client.enabled:
                raise ValueError(f"Client '{client_name}' not enabled or doesn't exist")

            # Create ticket
            return self.tickets.create_ticket(
                admin_id=admin.admin_id,
                client_id=client.client_id,
                text=text,
                executor=executor,
                comment=comment
            )

    def delete_ticket(
                self,
                admin_name: str,
                ticket_id: int
        ) -> None:
            """
            Business rule 5: Ticket can be deleted only by enabled Admin
            """
            # Check admin exists and enabled
            admin = self.admins.require_admin_by_name(admin_name)
            if admin.is_empty() or not admin.enabled:
                raise ValueError(f"Admin '{admin_name}' not enabled or doesn't exist")

            # Delete ticket
            self.tickets.delete_ticket(ticket_id, admin.admin_id)
