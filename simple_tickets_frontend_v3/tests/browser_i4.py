"""Administration checks on the loopback preview and a fresh --serve-i4 SQLite fixture."""

import argparse
import json
from pathlib import Path
import re
from secrets import token_hex
import unittest

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:5174"
API = f"{ORIGIN}/api/admin"
ACCOUNTS = None


class BrowserI4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = cls.enterClassContext(sync_playwright())
        cls.browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        cls.addClassCleanup(cls.browser.close)

    def page_for(self, profile, path):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id="UTC")
        self.addCleanup(context.close)
        errors = []
        self.addCleanup(lambda: self.assertEqual(errors, [], "Browser emitted uncaught JavaScript errors"))
        page = context.new_page()
        page.set_default_timeout(8_000)
        page.on("pageerror", lambda _: errors.append("uncaught page error"))
        page.goto(ORIGIN + path)
        page.get_by_label("Логин", exact=True).fill(ACCOUNTS[profile]["username"])
        password = page.get_by_label("Пароль", exact=True)
        password.fill(ACCOUNTS[profile]["password"])
        with page.expect_response(f"{API}/admins/permissions") as permissions:
            password.press("Enter")
        self.assertEqual(permissions.value.status, 200)
        return page

    @staticmethod
    def heading(page, text):
        return page.get_by_role("heading", level=1, name=text, exact=True)

    @staticmethod
    def button(page, text):
        return page.get_by_role("button", name=text, exact=True)

    def record_request(self, page, request_method, endpoint, button, status=200):
        with page.expect_response(lambda response: response.url == endpoint and
                                  response.request.method == request_method) as pending:
            button.click()
        response = pending.value
        self.assertEqual(response.status, status)
        return response

    def ticket_page(self, profile, scenario):
        ticket = ACCOUNTS["management"]["tickets"][scenario]
        page = self.page_for(profile, f"/tickets/{ticket['id']}")
        expect(self.heading(page, ticket["title"])).to_be_visible()
        return page, f"{API}/tickets/{ticket['id']}"

    def confirm(self, page):
        return self.button(page, "Подтвердить")

    def test_client_create_edit_and_read_only_access(self):
        page = self.page_for("catalog_operator", "/clients")
        expect(self.heading(page, "Клиенты")).to_be_visible()
        page.get_by_role("link", name="Создать клиента", exact=True).click()
        form = page.get_by_role("form", name="Создать клиента")
        title = f"Клиент браузера И4 {token_hex(4)}"
        form.get_by_role("textbox", name="Название", exact=True).fill(title)
        form.get_by_role("textbox", name="Адрес", exact=True).fill("Синтетический адрес")
        created = self.record_request(page, "POST", f"{API}/clients/", self.button(form, "Создать"), 201).json()
        self.assertEqual(created["name"], title)
        self.assertEqual(created["address"], "Синтетический адрес")
        path = f"/clients/{created['client_id']}"
        expect(page).to_have_url(ORIGIN + path)
        expect(self.heading(page, title)).to_be_visible()
        page.get_by_role("link", name="Редактировать", exact=True).click()
        edit = page.get_by_role("form", name="Редактирование записи")
        expect(edit.get_by_role("textbox", name="Название", exact=True)).to_have_value(title)
        edit.get_by_role("textbox", name="Описание", exact=True).fill("Перечитанная правка браузера")
        updated = self.record_request(page, "PUT", API + path + "/contact", self.button(edit, "Сохранить изменения")).json()
        self.assertEqual((updated["name"], updated["address"]), (title, "Синтетический адрес"))
        self.assertEqual(updated["description"], "Перечитанная правка браузера")
        viewer = self.page_for("catalog_reader", path)
        expect(self.heading(viewer, title)).to_be_visible()
        expect(viewer.get_by_text("Перечитанная правка браузера", exact=True)).to_be_visible()
        expect(viewer.get_by_role("link", name="Редактировать", exact=True)).to_have_count(0)
        expect(self.button(viewer, "Удалить запись")).to_have_count(0)

    def test_create_only_client_access_never_loads_catalog_or_detail(self):
        page = self.page_for("client_create", "/clients/new")
        reads = []
        page.on("request", lambda request: reads.append(request.url)
                if request.method == "GET" and request.url.startswith(f"{API}/clients/") else None)
        form = page.get_by_role("form", name="Создать клиента")
        form.get_by_role("textbox", name="Название", exact=True).fill(f"Клиент без просмотра {token_hex(4)}")
        created = self.record_request(page, "POST", f"{API}/clients/", self.button(form, "Создать"), 201).json()
        expect(page.get_by_role("status").filter(has_text=f"Запись № {created['client_id']} создана.")).to_be_visible()
        expect(page).to_have_url(ORIGIN + "/clients/new")
        expect(page.get_by_role("link", name="К списку", exact=True)).to_have_count(0)
        self.assertEqual(reads, [])

    def test_explicit_create_replay_uses_original_payload_key_and_record(self):
        page = self.page_for("client_create", "/clients/new")
        form = page.get_by_role("form", name="Создать клиента")
        name = form.get_by_role("textbox", name="Название", exact=True)
        title = f"Клиент повтора {token_hex(4)}"
        name.fill(title)
        endpoint = f"{API}/clients/"
        attempts = []
        committed = []

        def lose_first_response(route):
            request = route.request
            if request.method != "POST":
                route.continue_()
                return
            attempts.append((request.header_value("idempotency-key"), request.post_data_json))
            if len(attempts) > 1:
                route.continue_()
                return
            response = route.fetch()
            try:
                committed.append((response.status, response.json()["client_id"]))
            finally:
                response.dispose()
            route.abort()

        page.route(endpoint, lose_first_response)
        self.button(form, "Создать").click()
        repeat = self.button(page, "Повторить создание с тем же ключом")
        expect(repeat).to_be_visible()
        expect(self.button(form, "Создать")).to_be_disabled()
        expect(name).to_have_value(title)
        self.assertEqual(len(attempts), 1)
        replayed = self.record_request(page, "POST", endpoint, repeat, 201).json()
        self.assertEqual(committed, [(201, replayed["client_id"])])
        self.assertEqual(len(attempts), 2)
        self.assertTrue(attempts[0][0])
        self.assertEqual(attempts[0], attempts[1])
        expect(page.get_by_role("status").filter(has_text=f"Запись № {replayed['client_id']} создана.")).to_be_visible()
        viewer = self.page_for("catalog_reader", "/clients")
        expect(viewer.get_by_role("row").filter(has_text=title)).to_have_count(1)

    def test_account_attach_toggle_and_detach_are_distinct_commands(self):
        subject = ACCOUNTS["management"]["actors"]["account_subject"]
        page = self.page_for("catalog_operator", f"/admins/{subject}")
        expect(self.heading(page, "Сотрудник без аккаунта И4")).to_be_visible()
        endpoint = f"{API}/admins/{subject}/account"
        self.button(page, "Подключить аккаунт").click()
        username = "qa" + token_hex(6)
        page.get_by_role("textbox", name="Логин", exact=True).fill(username)
        password_input = page.get_by_label("Новый пароль", exact=True)
        expect(password_input).to_have_attribute("type", "password")
        password_input.fill("Aa1!" + token_hex(12))
        attached = self.record_request(page, "POST", endpoint, self.confirm(page)).json()
        self.assertEqual(attached["login"], username)
        self.assertTrue(attached["enabled_login"])
        self.assertNotIn("password", attached)
        expect(page.locator('input[type="password"]')).to_have_count(0)
        self.button(page, "Отключить доступ").click()
        disabled = self.record_request(page, "PATCH", endpoint + "/disable", self.confirm(page))
        self.assertIsNone(disabled.request.post_data)
        self.assertFalse(disabled.json()["enabled_login"])
        self.assertTrue(disabled.json()["enabled"])
        self.button(page, "Включить доступ").click()
        enabled = self.record_request(page, "PATCH", endpoint + "/enable", self.confirm(page))
        self.assertTrue(enabled.json()["enabled_login"])
        self.button(page, "Отвязать аккаунт").click()
        detached = self.record_request(page, "DELETE", endpoint, self.confirm(page))
        self.assertIsNone(detached.request.post_data)
        self.assertEqual(detached.json()["login"], "")
        expect(self.button(page, "Подключить аккаунт")).to_be_visible()

    def change_role(self, page, mode, role_name, endpoint, method):
        self.button(page, mode).click()
        page.get_by_role("checkbox", name=role_name, exact=False).check()
        return self.record_request(page, method, endpoint, self.confirm(page))

    def test_own_grant_and_revoke_refresh_permissions_without_profile_put(self):
        actor = ACCOUNTS["management"]["actors"]["admin_role_operator"]
        role = ACCOUNTS["management"]["roles"]["optional_admin"]
        page = self.page_for("admin_role_operator", f"/admins/{actor}")
        expect(self.heading(page, "Роли сотрудников И4")).to_be_visible()
        client_link = page.get_by_role("link", name="Клиенты", exact=True)
        expect(client_link).to_have_count(0)
        expect(page.get_by_role("link", name="Редактировать", exact=True)).to_have_count(0)
        expect(page.get_by_role("link", name="Роли пользователей", exact=True)).to_have_count(0)
        requests = []
        page.on("request", lambda request: requests.append((request.method, request.url)))
        endpoint = f"{API}/admins/{actor}/roles"
        with page.expect_response(f"{API}/admins/permissions") as permissions:
            grant = self.change_role(page, "Выдать роли", "Чтение клиентов И4", endpoint, "POST")
        self.assertEqual(grant.request.post_data_json, {"roles": [role]})
        self.assertIn("client.view", permissions.value.json()["permissions"])
        expect(client_link).to_be_visible()
        with page.expect_response(f"{API}/admins/permissions") as permissions:
            revoke = self.change_role(page, "Отозвать роли", "Чтение клиентов И4", endpoint, "DELETE")
        self.assertEqual(revoke.request.post_data_json, {"roles": [role]})
        self.assertNotIn("client.view", permissions.value.json()["permissions"])
        expect(client_link).to_have_count(0)
        self.assertEqual([item for item in requests if item[0] in {"POST", "PUT", "DELETE"}],
                         [("POST", endpoint), ("DELETE", endpoint)])

    def test_applied_grant_survives_uncertain_revoke_and_permissions_are_read_back(self):
        actor = ACCOUNTS["management"]["actors"]["catalog_reader"]
        roles = ACCOUNTS["management"]["roles"]
        page = self.page_for("catalog_operator", f"/admins/{actor}")
        expect(self.heading(page, "Читатель И4")).to_be_visible()
        detail = f"{API}/admins/{actor}"
        endpoint = detail + "/roles"
        grant = self.change_role(page, "Выдать роли", "Чтение клиентов И4", endpoint, "POST")
        self.assertIn(roles["optional_admin"], grant.json()["roles"])
        requests = []

        def interrupt_revoke(route):
            requests.append(route.request.post_data_json)
            route.abort()

        page.route(endpoint, interrupt_revoke)
        self.button(page, "Отозвать роли").click()
        page.get_by_role("checkbox", name="Читатель И4", exact=False).check()
        self.confirm(page).click()
        check = self.button(page, "Проверить состояние")
        expect(check).to_be_visible()
        with page.expect_response(lambda response: response.url == detail and response.request.method == "GET") as current:
            check.click()
        self.assertEqual(current.value.status, 200)
        self.assertEqual(set(current.value.json()["roles"]), {roles["optional_admin"], roles["assigned_admin"]})
        self.assertEqual(requests, [{"roles": [roles["assigned_admin"]]}])

    def test_protected_system_role_and_linked_client_cannot_be_deleted(self):
        role = ACCOUNTS["management"]["roles"]["system_admin"]
        page = self.page_for("admin_role_operator", f"/roles/admin/{role}")
        expect(self.heading(page, "Системная роль И4")).to_be_visible()
        expect(self.button(page, "Удалить запись")).to_have_count(0)
        expect(page.get_by_role("link", name="Редактировать", exact=True)).to_have_count(0)

        client_id = ACCOUNTS["management"]["references"]["client"]
        client = self.page_for("catalog_operator", f"/clients/{client_id}")
        expect(self.heading(client, "Тестовый клиент")).to_be_visible()
        self.button(client, "Удалить запись").click()
        dialog = client.get_by_role("dialog")
        expect(self.button(dialog, "Отмена")).to_be_focused()
        self.record_request(client, "DELETE", f"{API}/clients/{client_id}",
                            self.button(dialog, "Удалить без восстановления"), 400)
        expect(self.heading(client, "Тестовый клиент")).to_be_visible()
        expect(client.get_by_role("alert")).to_be_visible()

    def test_cancel_requires_reason_and_preserves_the_card(self):
        page, endpoint = self.ticket_page("cancel_operator", "cancel")
        expect(self.button(page, "Удалить заявку")).to_have_count(0)
        self.button(page, "Отменить заявку").click()
        form = page.get_by_role("form", name="Отменить заявку")
        reason = form.get_by_role("textbox", name="Причина", exact=True)
        self.confirm(form).click()
        expect(reason).to_be_focused()
        expect(reason).to_have_attribute("aria-invalid", "true")
        reason.fill("Синтетическая причина отмены в браузере")
        response = self.record_request(page, "PATCH", endpoint + "/cancel", self.confirm(form)).json()
        self.assertEqual(response["statuses"][-1]["status"], "cancelled")
        self.assertEqual(response["statuses"][-1]["comment"], "Синтетическая причина отмены в браузере")
        expect(page.locator('.badge[data-status="cancelled"]')).to_have_text("Отменено")
        expect(self.heading(page, ACCOUNTS["management"]["tickets"]["cancel"]["title"])).to_be_visible()
        expect(self.button(page, "Отменить заявку")).to_have_count(0)

    def test_delete_warning_and_lost_response_are_reconciled_without_replay(self):
        page, endpoint = self.ticket_page("delete_operator", "delete_linked")
        expect(self.button(page, "Отменить заявку")).to_have_count(0)
        action = self.button(page, "Удалить заявку")
        action.click()
        dialog = page.get_by_role("dialog", name="Удалить заявку")
        expect(dialog.get_by_text(re.compile("связанная заявка клиента", re.IGNORECASE))).to_be_visible()
        cancel = self.button(dialog, "Отмена")
        expect(cancel).to_be_focused()
        cancel.press("Escape")
        expect(dialog).to_have_count(0)
        expect(action).to_be_focused()
        attempts = []

        def lose_response(route):
            if route.request.method != "DELETE":
                route.continue_()
                return
            response = route.fetch()
            try:
                attempts.append((response.status, route.request.post_data))
            finally:
                response.dispose()
            route.abort()

        page.route(endpoint, lose_response)
        action.click()
        self.button(dialog, "Удалить без восстановления").click()
        check = self.button(page, "Проверить состояние")
        expect(check).to_be_visible()
        expect(dialog).to_have_count(0)
        expect(action).to_be_disabled()
        self.record_request(page, "GET", endpoint, check, 404)
        expect(self.heading(page, ACCOUNTS["management"]["tickets"]["delete_linked"]["title"])).to_have_count(0)
        self.assertEqual(attempts, [(204, None)])

    def test_unknown_delete_stays_locked_when_ticket_is_still_present(self):
        page, endpoint = self.ticket_page("delete_operator", "cancel_at_work")
        attempts = []

        def interrupt_delete(route):
            if route.request.method == "DELETE":
                attempts.append(route.request.post_data)
                route.abort()
            else:
                route.continue_()

        page.route(endpoint, interrupt_delete)
        action = self.button(page, "Удалить заявку")
        action.click()
        dialog = page.get_by_role("dialog", name="Удалить заявку")
        self.button(dialog, "Удалить без восстановления").click()
        check = self.button(page, "Проверить состояние")
        expect(check).to_be_visible()
        expect(dialog).to_have_count(0)
        self.record_request(page, "GET", endpoint, check)
        expect(page.get_by_role("alert").filter(has_text="удаления")).to_be_visible()
        expect(check).to_be_visible()
        expect(action).to_be_disabled()
        ticket = ACCOUNTS["management"]["tickets"]["cancel_at_work"]
        expect(self.heading(page, ticket["title"])).to_be_visible()
        self.button(page, f"Закрыть заявку № {ticket['id']}").click()
        close = page.get_by_role("dialog", name=f"Действие по заявке № {ticket['id']} не подтверждено")
        self.button(close, "Закрыть вкладку").click()
        row = page.get_by_role("row").filter(has_text=ticket["title"])
        row.get_by_role("link", name=f"№ {ticket['id']}", exact=True).click()
        expect(self.heading(page, ticket["title"])).to_be_visible()
        expect(action).to_be_disabled()
        expect(check).to_have_count(1)
        self.assertEqual(attempts, [None])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credentials", type=Path, help="private credentials file printed by --serve-i4")
    parser.add_argument("tests", nargs="*", help="optional unittest names")
    options = parser.parse_args()
    credentials = options.credentials.resolve()
    if (credentials.parent.parent != ROOT or not credentials.parent.name.startswith(".qa-contract-") or
            not (credentials.parent / "test.sqlite3").is_file() or credentials.name != "credentials.json"):
        parser.error("use the disposable loopback fixture credentials")
    ACCOUNTS = json.loads(credentials.read_text(encoding="utf-8"))
    if not isinstance(ACCOUNTS.get("management"), dict):
        parser.error("use credentials from --serve-i4")
    unittest.main(argv=[__file__, *options.tests], verbosity=2)
