from __future__ import annotations

import pytest

from src.domain.client import Client
from src.domain.exceptions import ItemValidationError

pytestmark = pytest.mark.unit


def test_client_create_builds_value_objects_and_creator() -> None:
    client = Client.create(
        client_id=10,
        name="Acme Corp",
        email="INFO@EXAMPLE.COM",
        address=" Main street ",
        phone=" 123 ",
        description=" Important customer ",
        created_by_admin_id=7,
    )
    assert client.client_id == 10
    assert str(client.name) == "Acme Corp"
    assert str(client.email) == "info@example.com"
    assert str(client.address) == "Main street"
    assert str(client.phone) == "123"
    assert str(client.description) == "Important customer"
    assert client.created_by_admin_id == 7


def test_client_rejects_negative_creator_id() -> None:
    with pytest.raises(ItemValidationError):
        Client.create(client_id=0, name="Acme", created_by_admin_id=-1)


def test_client_wraps_value_object_errors() -> None:
    with pytest.raises(ItemValidationError):
        Client.create(client_id=0, name="A")


def test_client_update_contact_info_can_replace_and_clear_optional_fields() -> None:
    client = Client.create(
        client_id=1,
        name="Acme",
        email="a@example.com",
        address="Street",
        phone="123",
        description="Old text",
    )
    client.update_contact_info(
        name="Acme New",
        email="",
        address="",
        phone="",
        description="New text",
    )
    assert client.get_contact_summary() == {
        "name": "Acme New",
        "email": "",
        "address": "",
        "phone": "",
        "description": "New text",
    }


def test_client_update_wraps_invalid_values() -> None:
    client = Client.create(client_id=1, name="Acme")
    with pytest.raises(ItemValidationError):
        client.update_contact_info(name="A")


def test_client_enable_disable_and_identity() -> None:
    client = Client.create(client_id=1, name="Acme")
    client.disable()
    assert not client.enabled
    client.enable()
    assert client.enabled
    assert client == Client.create(client_id=1, name="Other")
    assert client != Client.create(client_id=2, name="Acme")
