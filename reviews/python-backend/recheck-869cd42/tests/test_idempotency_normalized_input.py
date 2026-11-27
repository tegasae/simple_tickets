"""Check replay for input values normalized by the existing domain model."""
import secrets

import pytest

from test_idempotent_creations import counts, creation, expected_counts, post


@pytest.mark.parametrize(("case", "field"), [
    ("department", "name"),
    ("admin_with_account", "login"),
    ("user_with_account", "login"),
])
def test_domain_normalized_input_replays_saved_result(world, case, field):
    """201 на обе формы. Пробелы в имени отдела или логине не создают вторую запись."""
    command = creation(world, case)
    key = secrets.token_hex(16)
    before = counts(world, command)

    first = post(world, command, key)
    assert first.status_code == 201
    spaced = {**command.payload, field: f" {command.payload[field]} "}
    replay = post(world, command, key, spaced)

    assert counts(world, command) == expected_counts(before, command)
    assert replay.status_code == first.status_code
    assert replay.json() == first.json()


@pytest.mark.parametrize("case", ["admin", "user"])
def test_employee_name_and_contact_values_use_domain_normalization(world, case):
    """Внешние пробелы и регистр email сохраняют эквивалентный результат, Employee создаётся один раз."""
    command = creation(world, case)
    key = secrets.token_hex(16)
    before = counts(world, command)
    original = {
        **command.payload,
        "last_name": "Synthetic surname",
        "email": "operator@example.invalid",
        "phone": "+1 555 0100",
    }
    equivalent = {
        **original,
        "first_name": " " + original["first_name"] + " ",
        "last_name": " Synthetic surname ",
        "email": " OPERATOR@EXAMPLE.INVALID ",
        "phone": " +1 555 0100 ",
    }

    first = post(world, command, key, original)
    replay = post(world, command, key, equivalent)

    assert first.status_code == replay.status_code == 201
    assert replay.json() == first.json()
    assert counts(world, command) == expected_counts(before, command)


def test_client_address_contact_and_description_use_domain_normalization(world):
    """Адрес, email, телефон и описание нормализуются как в домене. Повтор возвращает исходный Client."""
    command = creation(world, "client")
    key = secrets.token_hex(16)
    before = counts(world, command)
    original = {
        **command.payload,
        "address": "Synthetic address",
        "email": "office@example.invalid",
        "phone": "+1 555 0101",
    }
    equivalent = {
        **original,
        "address": " Synthetic address ",
        "email": " OFFICE@EXAMPLE.INVALID ",
        "phone": " +1 555 0101 ",
        "description": " ",
    }

    first = post(world, command, key, original)
    replay = post(world, command, key, equivalent)

    assert first.status_code == replay.status_code == 201
    assert replay.json() == first.json()
    assert counts(world, command) == expected_counts(before, command)


@pytest.mark.parametrize(("case", "optional_fields"), [
    ("client", ("email", "address", "phone")),
    ("admin", ("last_name", "email", "phone", "login")),
    ("user", ("last_name", "email", "phone", "login")),
])
def test_invalid_whitespace_only_value_does_not_match_omitted_value(world, case, optional_fields):
    """Незаполненное поле отличается от пробельного. Обычный ввод даёт 400, повтор ключа 409."""
    command = creation(world, case)
    key = secrets.token_hex(16)
    before = counts(world, command)

    assert post(world, command, key).status_code == 201
    for field in optional_fields:
        invalid = {**command.payload, field: " "}
        assert post(world, command, payload=invalid).status_code == 400
        assert post(world, command, key, invalid).status_code == 409

    assert counts(world, command) == expected_counts(before, command)


@pytest.mark.parametrize(("case", "plain_field"), [
    ("admin_role", "description"),
    ("user_role", "description"),
    ("admin", "job_title"),
])
def test_whitespace_preserved_by_business_field_remains_significant(world, case, plain_field):
    """Пробелы в поле без доменной нормализации меняют запрос, ответ 409, записи неизменны."""
    command = creation(world, case)
    key = secrets.token_hex(16)
    before = counts(world, command)
    original = {**command.payload, plain_field: "Synthetic text"}

    first = post(world, command, key, original)
    assert first.status_code == 201
    changed = {**original, plain_field: " Synthetic text "}
    assert post(world, command, key, changed).status_code == 409
    assert counts(world, command) == expected_counts(before, command)


def test_different_password_is_a_conflict_with_the_same_login(world):
    """Изменённый пароль при том же ключе даёт 409, версия создания Account сохраняется."""
    command = creation(world, "admin_with_account")
    key = secrets.token_hex(16)
    before = counts(world, command)

    assert post(world, command, key).status_code == 201
    changed = {**command.payload, "password": "Aa1!" + secrets.token_hex(12)}
    assert post(world, command, key, changed).status_code == 409
    assert counts(world, command) == expected_counts(before, command)
