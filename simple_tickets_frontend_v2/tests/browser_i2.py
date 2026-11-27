"""I2 browser checks on the local production build and disposable SQLite fixture.

Run the I1 browser suite first or start a new fixture before rerunning I1.
These checks create and edit records in the fixture.
"""

import argparse
import json
from pathlib import Path
import re
from secrets import token_hex
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:5174"
API = f"{ORIGIN}/api/admin"
TICKETS = f"{API}/tickets"
ACCOUNTS = None


def synthetic_text(prefix):
    return f"{prefix} {token_hex(4)}"


class BrowserI2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = cls.enterClassContext(sync_playwright())
        cls.browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        cls.addClassCleanup(cls.browser.close)

    def page(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.addCleanup(context.close)
        errors = []
        self.addCleanup(lambda: self.assertEqual(errors, [], "Browser emitted uncaught JavaScript errors"))
        page = context.new_page()
        page.on("pageerror", lambda _: errors.append("uncaught page error"))
        return page

    def login(self, page, profile, path):
        page.goto(ORIGIN + path)
        page.get_by_label("Логин", exact=True).fill(ACCOUNTS[profile]["username"])
        password = page.get_by_label("Пароль", exact=True)
        password.fill(ACCOUNTS[profile]["password"])
        with page.expect_response(f"{API}/admins/permissions") as permissions:
            password.press("Enter")
        self.assertEqual(permissions.value.status, 200)

    @staticmethod
    def ticket_title(page, title):
        return page.get_by_role("heading", level=1, name=title, exact=True)

    def open_queue_ticket(self, page, title):
        row = page.get_by_role("row").filter(has=page.get_by_text(title, exact=True))
        row.get_by_role("link").click()
        expect(self.ticket_title(page, title)).to_be_visible()

    @staticmethod
    def editor(page):
        return page.get_by_role("form", name="Изменение заявки")

    def open_editor(self, page):
        page.get_by_role("button", name="Редактировать заявку", exact=True).click()
        form = self.editor(page)
        expect(form).to_be_visible()
        return form

    @staticmethod
    def save(form):
        form.get_by_role("button", name="Сохранить изменения", exact=True).click()

    @staticmethod
    def choose_client(form):
        field = form.get_by_role("combobox", name="Клиент", exact=True)
        field.fill("Тестовый клиент")
        expect(form.get_by_role("option", name=re.compile(r"^Тестовый клиент · № \d+$"))).to_be_visible()
        field.press("ArrowDown")
        field.press("Enter")

    def change_description_elsewhere(self, page, endpoint, description):
        auth = page.request.post(f"{ORIGIN}/api/auth/admin/login", form=ACCOUNTS["writer"])
        self.assertEqual(auth.status, 200)
        tokens = auth.json()
        changed = page.request.patch(endpoint, headers={"Authorization": f"Bearer {tokens['access_token']}"},
                                     data={"description": description})
        self.assertEqual(changed.status, 200)

    @staticmethod
    def lose_patch_response(page, endpoint):
        writes = []

        def drop_write_response(route):
            writes.append(route.fetch().status)
            route.abort()

        page.route(endpoint, drop_write_response)
        return writes

    def test_reader_does_not_get_write_controls(self):
        page = self.page()
        self.login(page, "reader", "/tickets/1")
        expect(self.ticket_title(page, "Проверка печати")).to_be_visible()
        expect(page.get_by_role("button", name="Редактировать заявку")).to_have_count(0)
        expect(page.get_by_role("form", name="Добавить комментарий")).to_have_count(0)
        expect(page.get_by_role("link", name="Новая заявка", exact=True)).to_have_count(0)

    def test_two_drafts_survive_linked_navigation_and_save_and_dirty_close(self):
        page = self.page()
        self.login(page, "writer", "/tickets?queue=open")
        self.open_queue_ticket(page, "Проверка печати")
        first_draft = synthetic_text("Правка первой заявки в I2")
        self.open_editor(page).get_by_label("Описание", exact=True).fill(first_draft)

        page.get_by_role("link", name="Заявки", exact=True).click()
        self.open_queue_ticket(page, "Очередь поддержки")
        second_draft = "Отдельный черновик второй заявки"
        self.open_editor(page).get_by_label("Описание", exact=True).fill(second_draft)

        client = page.get_by_role("link", name=re.compile(r"^Клиент № \d+$"))
        client.focus()
        client.press("Enter")
        expect(page.get_by_text("Тестовый клиент", exact=True).first).to_be_visible()
        page.get_by_role("link", name="К заявке № 2", exact=True).click()
        expect(client).to_be_focused()
        expect(self.editor(page).get_by_label("Описание", exact=True)).to_have_value(second_draft)

        workspace = page.get_by_role("navigation", name="Открытые заявки")
        first_tab = workspace.get_by_role("link", name=re.compile(r"^№ 1\b"))
        second_tab = workspace.get_by_role("link", name=re.compile(r"^№ 2\b"))
        expect(first_tab).to_have_count(1)
        expect(second_tab).to_have_count(1)
        first_tab.click()
        first_editor = self.editor(page)
        expect(first_editor.get_by_label("Описание", exact=True)).to_have_value(first_draft)
        with page.expect_response(lambda response: response.url == f"{TICKETS}/1/description" and
                                 response.request.method == "PATCH") as saved:
            self.save(first_editor)
        self.assertEqual(saved.value.status, 200)
        self.assertEqual(saved.value.json()["description"], first_draft)
        expect(page.get_by_text("Изменения сохранены.", exact=True)).to_be_visible()

        second_tab.click()
        expect(self.editor(page).get_by_label("Описание", exact=True)).to_have_value(second_draft)
        close = workspace.get_by_role("button", name="Закрыть заявку № 2", exact=True)
        close.click()
        dialog = page.get_by_role("dialog", name="Несохранённые изменения в заявке № 2", exact=True)
        expect(dialog).to_be_visible()
        continue_button = dialog.get_by_role("button", name="Продолжить редактирование", exact=True)
        expect(continue_button).to_be_focused()
        dialog.get_by_role("button", name="Отбросить черновик", exact=True).press("Tab")
        expect(dialog.get_by_role("button", name="Сохранить и закрыть", exact=True)).to_be_focused()
        continue_button.press("Enter")
        expect(self.editor(page).get_by_label("Описание", exact=True)).to_have_value(second_draft)
        close.click()
        dialog.get_by_role("button", name="Отбросить черновик", exact=True).click()
        expect(second_tab).to_have_count(0)

    def test_save_and_close_waits_for_server_confirmation(self):
        page = self.page()
        self.login(page, "writer", "/tickets/2")
        expect(self.ticket_title(page, "Очередь поддержки")).to_be_visible()
        value = synthetic_text("Правка при закрытии")
        self.open_editor(page).get_by_label("Описание", exact=True).fill(value)
        workspace = page.get_by_role("navigation", name="Открытые заявки")
        workspace.get_by_role("button", name="Закрыть заявку № 2", exact=True).click()
        dialog = page.get_by_role("dialog", name="Несохранённые изменения в заявке № 2", exact=True)
        with page.expect_response(lambda response: response.url == f"{TICKETS}/2/description" and
                                 response.request.method == "PATCH") as saved:
            dialog.get_by_role("button", name="Сохранить и закрыть", exact=True).click()
        self.assertEqual(saved.value.status, 200)
        self.assertEqual(saved.value.json()["description"], value)
        expect(workspace).to_have_count(0)
        expect(page.get_by_role("heading", name="Заявки", exact=True)).to_be_visible()
        self.open_queue_ticket(page, "Очередь поддержки")
        expect(page.get_by_text(value, exact=True)).to_be_visible()

    def test_creator_validation_and_real_creation_without_view(self):
        page = self.page()
        reads = []
        page.on("request", lambda request: reads.append(urlsplit(request.url).path)
                if request.method == "GET" and urlsplit(request.url).path.startswith("/api/admin/tickets") else None)
        self.login(page, "creator", "/")
        form = page.get_by_role("form", name="Новая заявка", exact=True)
        expect(form).to_be_visible()
        expect(page.get_by_role("heading", name="Новая заявка", exact=True)).to_be_focused()
        self.choose_client(form)
        subject = form.get_by_role("textbox", name="Тема заявки", exact=True)
        title = synthetic_text("Создана автором без права просмотра")
        subject.fill(title)

        # Hold a synthetic field error at the browser boundary, then use the actual create endpoint.
        path = f"{TICKETS}/"
        page.route(path, lambda route: route.fulfill(status=422, json={"detail": [
            {"loc": ["body", "text_of_ticket"], "msg": "Synthetic validation", "type": "value_error"},
        ]}))
        form.get_by_role("button", name="Создать заявку", exact=True).click()
        expect(subject).to_have_attribute("aria-invalid", "true")
        expect(subject).to_have_value(title)
        page.unroute(path)

        revised = title + " — повтор формы"
        subject.fill(revised)
        with page.expect_response(lambda response: response.url == path and response.request.method == "POST") as created:
            form.get_by_role("button", name="Создать заявку", exact=True).click()
        self.assertEqual(created.value.status, 201)
        ticket = created.value.json()
        self.assertEqual(ticket["text_of_ticket"], revised)
        expect(page.get_by_text(f"Заявка № {ticket['ticket_id']} создана.", exact=True)).to_be_visible()
        expect(page.get_by_role("link", name=re.compile(r"^Открыть заявку"))).to_have_count(0)
        self.assertEqual(reads, [], "Creation without ticket.view must not read a ticket or queue")

    def test_conflict_preserves_draft_and_sends_no_mutation(self):
        page = self.page()
        self.login(page, "writer", "/tickets/1")
        expect(self.ticket_title(page, "Проверка печати")).to_be_visible()
        form = self.open_editor(page)
        local = synthetic_text("Моя правка перед сверкой")
        field = form.get_by_label("Описание", exact=True)
        field.fill(local)

        # Another synthetic writer session changes the persisted baseline.
        remote = synthetic_text("Серверная правка другого сеанса")
        endpoint = f"{TICKETS}/1/description"
        self.change_description_elsewhere(page, endpoint, remote)

        writes = []
        page.on("request", lambda request: writes.append(1)
                if request.method == "PATCH" and request.url == endpoint else None)
        self.save(form)
        expect(page.get_by_text("На сервере изменились поля, которые вы редактируете.", exact=True)).to_be_visible()
        expect(page.get_by_text(f"На сервере: {remote}", exact=True)).to_be_visible()
        expect(field).to_have_value(local)
        self.assertEqual(writes, [], "A conflicting pre-read must precede any write")

    def test_patch_lost_response_requires_readback_without_automatic_retry(self):
        page = self.page()
        self.login(page, "writer", "/tickets/1")
        expect(self.ticket_title(page, "Проверка печати")).to_be_visible()
        form = self.open_editor(page)
        description = synthetic_text("Изменение с потерянным ответом сервера")
        form.get_by_label("Описание", exact=True).fill(description)
        endpoint = f"{TICKETS}/1/description"
        writes = self.lose_patch_response(page, endpoint)
        self.save(form)
        check = page.get_by_role("button", name="Проверить результат", exact=True)
        expect(check).to_be_visible()
        self.assertEqual(writes, [200], "An uncertain PATCH must not auto-resend")

        with page.expect_response(lambda response: response.url == f"{TICKETS}/1" and
                                 response.request.method == "GET") as checked:
            check.click()
        self.assertEqual(checked.value.status, 200)
        self.assertEqual(checked.value.json()["description"], description)
        expect(page.get_by_text("Изменения сохранены.", exact=True)).to_be_visible()
        self.assertEqual(writes, [200], "Checking the uncertain result must only read the ticket")

    def test_uncertain_patch_keeps_draft_when_matching_readback_becomes_stale(self):
        page = self.page()
        self.login(page, "writer", "/tickets/1")
        expect(self.ticket_title(page, "Проверка печати")).to_be_visible()
        form = self.open_editor(page)
        field = form.get_by_label("Описание", exact=True)
        description = synthetic_text("Намерение до потери ответа")
        field.fill(description)

        endpoint = f"{TICKETS}/1/description"
        writes = self.lose_patch_response(page, endpoint)
        with page.expect_response(lambda response: writes == [200] and response.url == f"{TICKETS}/1" and
                                 response.request.method == "GET") as readback:
            self.save(form)
        self.assertEqual(readback.value.status, 200)
        self.assertEqual(readback.value.json()["description"], description)
        check = page.get_by_role("button", name="Проверить результат", exact=True)
        expect(check).to_be_visible()
        self.assertEqual(writes, [200])

        remote = synthetic_text("Более поздняя серверная правка")
        self.change_description_elsewhere(page, endpoint, remote)
        check.click()
        expect(page.get_by_text("На сервере изменились поля, которые вы редактируете.", exact=True)).to_be_visible()
        expect(page.get_by_text(f"На сервере: {remote}", exact=True)).to_be_visible()
        expect(page.get_by_text(f"В черновике: {description}", exact=True)).to_be_visible()
        expect(field).to_have_value(description)
        self.assertEqual(writes, [200], "Manual readback must not replay the uncertain write")

    def test_comment_lost_response_requires_manual_idempotent_replay(self):
        page = self.page()
        self.login(page, "writer", "/tickets/1")
        expect(self.ticket_title(page, "Проверка печати")).to_be_visible()
        composer = page.get_by_role("form", name="Добавить комментарий", exact=True)
        comment = composer.get_by_label("Комментарий", exact=True)
        message = synthetic_text("Комментарий с проверяемым повтором")
        comment.fill(message)
        posts = []
        forwarded = []

        def discard_first_response(route):
            request = route.request
            posts.append((request.headers.get("idempotency-key"), request.post_data_json))
            if len(posts) == 1:
                forwarded.append(route.fetch().status)
                route.abort()
            else:
                route.continue_()

        path = f"{TICKETS}/1/comments"
        page.route(path, discard_first_response)
        composer.get_by_role("button", name="Добавить комментарий", exact=True).click()
        repeat = page.get_by_role("button", name="Повторить отправку", exact=True)
        expect(repeat).to_be_visible()
        expect(comment).to_have_value(message)
        self.assertEqual(forwarded, [200], "The test must lose the response after a real write")
        self.assertEqual(len(posts), 1, "A lost response must not silently retry POST")
        repeat.click()
        expect(page.get_by_text(message, exact=True)).to_have_count(1)
        expect(comment).to_have_value("")
        self.assertEqual(len(posts), 2)
        self.assertTrue(posts[0][0] and posts[0] == posts[1], "Manual retry must keep original key and JSON")

        another = synthetic_text("Следующий отдельный комментарий")
        comment.fill(another)
        composer.get_by_role("button", name="Добавить комментарий", exact=True).click()
        expect(page.get_by_text(another, exact=True)).to_have_count(1)
        expect(page.get_by_text(message, exact=True)).to_have_count(1)
        self.assertEqual(len(posts), 3)
        self.assertTrue(posts[2][0] and posts[2][0] != posts[0][0], "A new comment requires a new key")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credentials", type=Path, help="private credentials file printed by the local fixture")
    options = parser.parse_args()
    credentials = options.credentials.resolve()
    if (credentials.parent.parent != ROOT or not credentials.parent.name.startswith(".qa-contract-") or
            not (credentials.parent / "test.sqlite3").is_file() or credentials.name != "credentials.json"):
        parser.error("use the disposable loopback fixture credentials")
    ACCOUNTS = json.loads(credentials.read_text(encoding="utf-8"))
    unittest.main(argv=[__file__], verbosity=2)
