import pytest

from src.domain.client import Client
from src.domain.exceptions import ItemValidationError


def test_client_create_and_update_contact_info():
    client = Client.create(
        client_id=1,
        name="Acme",
        email="info@acme.com",
        address="Main street",
        phone="123",
        created_by_admin_id=10,
    )

    client.update_contact_info(email="support@acme.com", phone="456")

    assert str(client.name) == "Acme"
    assert str(client.email) == "support@acme.com"
    assert str(client.phone) == "456"


def test_client_can_be_disabled_and_enabled():
    client = Client.create(client_id=1, name="Acme")

    client.disable()
    assert client.enabled is False

    client.enable()
    assert client.enabled is True


def test_client_rejects_negative_created_by_admin_id():
    with pytest.raises(ItemValidationError):
        Client.create(client_id=1, name="Acme", created_by_admin_id=-1)
