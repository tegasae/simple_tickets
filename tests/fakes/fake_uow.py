from tests.fakes.fake_repository import FakeRepository


class FakeUnitOfWork:
    def __init__(self):
        self.admins = FakeRepository("employee_id")
        self.users = FakeRepository("employee_id")
        self.clients = FakeRepository("client_id")
        self.tickets = FakeRepository("ticket_id")
        self.user_tickets = FakeRepository("ticket_id")
        self.roles_admin = FakeRepository("role_id")
        self.roles_user = FakeRepository("role_id")

        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True