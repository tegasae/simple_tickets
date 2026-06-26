class FakeRepository:
    def __init__(self, id_field: str):
        self.id_field = id_field
        self.items = {}
        self.next_id = 1

    def save(self, entity=None, **kwargs):
        if entity is None:
            entity = next(iter(kwargs.values()), None)

        if entity is None:
            raise TypeError("FakeRepository.save() expected an entity")

        entity_id = getattr(entity, self.id_field)

        if entity_id is None or entity_id == 0:
            entity_id = self.next_id
            setattr(entity, self.id_field, entity_id)
            self.next_id += 1

        self.items[int(entity_id)] = entity
        return entity

    def get(self, entity_id=None, **kwargs):
        if entity_id is None:
            entity_id = (
                    kwargs.get(self.id_field)
                    or kwargs.get("admin_id")
                    or kwargs.get("user_id")
                    or kwargs.get("employee_id")
                    or kwargs.get("client_id")
                    or kwargs.get("ticket_id")
                    or kwargs.get("role_id")
            )

        if entity_id is None or entity_id == 0:
            raise KeyError(f"Invalid entity id: {entity_id}")

        return self.items[int(entity_id)]



    def get_all(self):
        return list(self.items.values())

    def get_all_by_client_id(
            self,
            *,
            client_id: int,
    ):
        return [
            entity
            for entity in self.items.values()
            if getattr(entity, "client_id", None) == client_id
        ]

    def delete(self, entity_id):
        del self.items[int(entity_id)]

    def exist_login(self, login: str) -> bool:
        return any(
            getattr(getattr(entity, "account", None), "login", None) == login
            or getattr(getattr(getattr(entity, "account", None), "login", None), "value", None) == login
            for entity in self.items.values()
        )

    def exist_email(self, email: str) -> bool:
        return any(
            getattr(entity, "email", None) == email
            or getattr(getattr(entity, "email", None), "value", None) == email
            for entity in self.items.values()
        )

    def does_client_exist(self, client_id: int) -> bool:
        return any(
            getattr(entity, "client_id", None) == client_id
            for entity in self.items.values()
        )

    def does_user_exist(self, user_id: int) -> bool:
        return any(
            getattr(entity, "user_id", None) == user_id
            or getattr(entity, "contact_user_id", None) == user_id
            for entity in self.items.values()
        )

    def iter_active_by_client_id(
            self,
            *,
            client_id: int,
            batch_size: int,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        tickets = [
            ticket
            for ticket in self.items.values()
            if getattr(ticket, "client_id", None) == client_id
               and not ticket.is_terminal()
        ]

        for start in range(0, len(tickets), batch_size):
            yield tickets[start:start + batch_size]