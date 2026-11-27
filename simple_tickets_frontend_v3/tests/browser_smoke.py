"""Browser checks against the isolated deployment of the I1 production build."""

import argparse
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:5174"
REFRESH_KEY = "simple-tickets.v3.refresh"
ACCOUNTS = None
SCREENSHOTS = None


class BrowserSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = cls.enterClassContext(sync_playwright())
        cls.browser = playwright.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
        )
        cls.addClassCleanup(cls.browser.close)

    def page(self, width=1440, height=900):
        context = self.browser.new_context(viewport={"width": width, "height": height})
        self.addCleanup(context.close)
        errors = []
        self.addCleanup(lambda: self.assertEqual(errors, [], "Browser emitted uncaught JavaScript errors"))
        page = context.new_page()
        page.on("pageerror", lambda _: errors.append("uncaught page error"))
        return page

    @staticmethod
    def login(page, profile):
        page.get_by_label("Логин", exact=True).fill(ACCOUNTS[profile]["username"])
        password = page.get_by_label("Пароль", exact=True)
        password.fill(ACCOUNTS[profile]["password"])
        password.press("Enter")

    @staticmethod
    def capture(page, name):
        if SCREENSHOTS is not None:
            page.screenshot(path=str(SCREENSHOTS / name), animations="disabled")

    def test_reader_search_keyboard_card_back_reload_and_logout(self):
        page = self.page()
        page.goto(ORIGIN + "/tickets?queue=open")
        expect(page.get_by_role("heading", name="Вход сотрудника")).to_be_visible()
        self.capture(page, "i1-login.png")
        self.login(page, "reader")
        rows = page.get_by_role("row")
        expect(rows).to_have_count(3)
        self.capture(page, "i1-queue.png")

        sort = page.get_by_role("button", name="Дата создания")
        sort.focus()
        sort.press("Enter")
        expect(page.get_by_role("columnheader", name="Дата создания")).to_have_attribute("aria-sort", "ascending")
        search = page.get_by_role("searchbox", name="Поиск заявок")
        search.fill("Принято")
        search.press("Enter")
        expect(rows).to_have_count(2)
        self.assertNotIn("search", urlsplit(page.url).query)

        ticket_link = page.locator("tbody .ticket-link")
        ticket_href = ticket_link.get_attribute("href")
        ticket_link.focus()
        ticket_link.press("Enter")
        expect(page.get_by_role("heading", name="Проверка печати")).to_be_visible()
        expect(page.get_by_text("Синтетический комментарий")).to_be_visible()
        self.capture(page, "i1-ticket.png")
        page.get_by_role("button", name="История").click()
        expect(page.get_by_text("Создана", exact=True)).to_be_visible()

        page.go_back()
        expect(search).to_have_value("Принято")
        expect(ticket_link).to_be_focused()
        ticket_link.press("Enter")
        expect(page.get_by_role("heading", name="Проверка печати")).to_be_visible()
        old_refresh = page.evaluate("(key) => !!sessionStorage.getItem(key)", REFRESH_KEY)
        self.assertTrue(old_refresh)
        page.reload()
        expect(page.get_by_role("heading", name="Проверка печати")).to_be_visible()
        self.assertEqual(urlsplit(page.url).path, ticket_href)

        page.get_by_role("button", name="Выйти").click()
        expect(page.get_by_role("heading", name="Вход сотрудника")).to_be_visible()
        self.assertFalse(page.evaluate("(key) => !!sessionStorage.getItem(key)", REFRESH_KEY))

    def test_same_origin_popup_rotates_copied_refresh_and_opener_requires_login_after_reload(self):
        page = self.page()
        page.goto(ORIGIN + "/tickets?queue=open")
        self.login(page, "reader")
        expect(page.get_by_role("table", name="Заявки")).to_be_visible()
        refresh_url = ORIGIN + "/api/auth/admin/refresh"
        with page.context.expect_event("response", predicate=lambda response: response.url == refresh_url) as rotated:
            with page.expect_popup() as opened:
                page.evaluate("() => { window.open(location.href); }")
            popup = opened.value
        self.assertEqual(rotated.value.status, 200)
        expect(popup.get_by_role("table", name="Заявки")).to_be_visible()
        self.assertTrue(popup.evaluate("""(key) => {
            const initial = window.opener?.sessionStorage.getItem(key);
            const rotated = sessionStorage.getItem(key);
            return Boolean(initial && rotated && initial !== rotated);
        }""", REFRESH_KEY))

        protected_requests = []
        page.on("request", lambda request: protected_requests.append(urlsplit(request.url).path)
                if "/api/admin/tickets" in urlsplit(request.url).path else None)
        with page.expect_response(refresh_url) as rejected:
            page.reload()
        self.assertEqual(rejected.value.status, 401)
        expect(page.get_by_role("heading", name="Вход сотрудника")).to_be_visible()
        expect(page.get_by_role("table", name="Заявки")).to_have_count(0)
        self.assertFalse(page.evaluate("(key) => !!sessionStorage.getItem(key)", REFRESH_KEY))
        self.assertEqual(protected_requests, [])

        popup.get_by_role("row").filter(has_text="Проверка печати").get_by_role("link").click()
        expect(popup.get_by_role("heading", name="Проверка печати")).to_be_visible()
        with popup.expect_response(refresh_url) as still_active:
            popup.reload()
        self.assertEqual(still_active.value.status, 200)
        expect(popup.get_by_role("heading", name="Проверка печати")).to_be_visible()

    def test_invalid_login_returns_keyboard_focus_to_password_for_retry(self):
        page = self.page()
        page.goto(ORIGIN + "/tickets/1")
        username = page.get_by_label("Логин", exact=True)
        password = page.get_by_label("Пароль", exact=True)
        username.fill(ACCOUNTS["reader"]["username"])
        password.fill("Aa1!IncorrectSyntheticPassword")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        submit = page.get_by_role("button", name="Войти", exact=True)
        expect(submit).to_be_focused()
        login_url = ORIGIN + "/api/auth/admin/login"
        with page.expect_response(login_url) as rejected:
            page.keyboard.press("Enter")
        self.assertEqual(rejected.value.status, 401)
        expect(page.get_by_role("alert")).to_contain_text("Не удалось войти. Проверьте логин и пароль.")
        expect(password).to_have_value("")
        expect(password).to_be_focused()
        self.assertTrue(username.input_value() == ACCOUNTS["reader"]["username"], "login name was not retained")
        password.fill(ACCOUNTS["reader"]["password"])
        with page.expect_response(login_url) as accepted:
            password.press("Enter")
        self.assertEqual(accepted.value.status, 200)
        expect(page.get_by_role("heading", name="Проверка печати")).to_be_visible()

    def test_restricted_admin_direct_route_makes_no_ticket_request(self):
        page = self.page()
        ticket_requests = []
        page.on("request", lambda request: ticket_requests.append("ticket request")
                if "/api/admin/tickets" in urlsplit(request.url).path else None)
        page.goto(ORIGIN + "/tickets/1")
        self.login(page, "restricted")
        expect(page.get_by_role("heading", name="Нет доступа")).to_be_visible()
        self.assertEqual(ticket_requests, [])
        expect(page.get_by_role("table")).to_have_count(0)
        retry = page.get_by_role("button", name="Повторить")
        with page.expect_response("**/api/admin/admins/permissions"):
            retry.press("Enter")
        expect(retry).to_be_focused()
        self.assertEqual(ticket_requests, [])
        page.get_by_role("button", name="Выйти").click()
        expect(page.get_by_role("heading", name="Вход сотрудника")).to_be_visible()

    def test_real_404_and_recovery_from_interrupted_queue_request_at_320px(self):
        page = self.page(width=320, height=750)
        page.goto(ORIGIN + "/tickets/999999")
        self.login(page, "reader")
        expect(page.get_by_text("Заявка не найдена. Вернитесь к списку заявок.")).to_be_visible()
        page.route("**/api/admin/tickets/open", lambda route: route.abort())
        page.get_by_role("link", name="К списку заявок").click()
        expect(page.get_by_role("alert")).to_contain_text("Не удалось связаться с сервером")
        page.unroute("**/api/admin/tickets/open")
        page.get_by_role("button", name="Повторить").click()
        expect(page.get_by_role("table")).to_be_visible()
        expect(page.get_by_role("heading", level=1, name="Заявки")).to_be_focused()
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        self.capture(page, "i1-queue-narrow.png")

    def test_revoked_scope_clears_cached_results_when_permission_reload_fails(self):
        page = self.page()
        page.goto(ORIGIN + "/tickets?queue=open")
        self.login(page, "reader")
        expect(page.get_by_role("table")).to_be_visible()
        page.get_by_text("Фильтры", exact=True).click()
        page.get_by_label("Статус", exact=True).select_option("accepted")
        page.get_by_role("button", name="Убрать фильтр статуса").press("Enter")
        expect(page.locator("summary")).to_be_focused()
        ticket_link = page.locator("tbody .ticket-link").first
        ticket_href = ticket_link.get_attribute("href")
        detail = "**/api/admin" + ticket_href
        permissions = "**/api/admin/admins/permissions"
        page.route(detail, lambda route: route.fulfill(status=403, json={"detail": "Test denial"}))
        page.route(permissions, lambda route: route.fulfill(status=503, json={"detail": "Test unavailable"}))
        ticket_link.click()
        expect(page.get_by_text("Нет доступа", exact=True)).to_be_visible()
        page.go_back()
        expect(page.get_by_text("Нет доступа", exact=True)).to_be_visible()
        expect(page.get_by_role("table")).to_have_count(0)
        with page.expect_response(permissions):
            page.get_by_role("button", name="Повторить").click()
        expect(page.get_by_role("alert")).to_contain_text("Сервис временно недоступен")
        page.unroute(permissions)
        page.unroute(detail)
        page.get_by_role("button", name="Повторить").click()
        expect(page.get_by_role("table")).to_be_visible()

    def test_persistent_ticket_403_does_not_start_an_automatic_retry_loop(self):
        page = self.page()
        denials = []
        closed = "**/api/admin/tickets/closed"
        def deny(route):
            denials.append(1)
            route.fulfill(status=403, json={"detail": "Test denial"})

        page.route(closed, deny)
        page.goto(ORIGIN + "/tickets?queue=closed")
        self.login(page, "reader")
        expect(page.get_by_role("heading", name="Нет доступа")).to_be_visible()
        page.wait_for_timeout(300)
        self.assertEqual(len(denials), 1)
        with page.expect_response(closed):
            page.get_by_role("button", name="Повторить").click()
        expect(page.get_by_role("heading", name="Нет доступа")).to_be_visible()
        page.wait_for_timeout(300)
        self.assertEqual(len(denials), 2)

    def test_keyboard_pagination_and_empty_search_announcements(self):
        page = self.page()
        def fill_queue(route):
            source = route.fetch().json()[0]
            rows = [dict(source, ticket_id=number) for number in range(1, 32)]
            route.fulfill(status=200, json=rows)

        page.route("**/api/admin/tickets/open", fill_queue)
        page.goto(ORIGIN + "/tickets?queue=open")
        self.login(page, "reader")
        table = page.get_by_role("table", name="Заявки")
        expect(table.get_by_role("row")).to_have_count(26)
        next_button = page.get_by_role("button", name="Далее")
        next_button.press("Enter")
        expect(table.get_by_role("row")).to_have_count(7)
        expect(next_button).to_have_attribute("aria-disabled", "true")
        expect(next_button).to_be_focused()
        search = page.get_by_role("searchbox", name="Поиск заявок")
        search.fill("Заявка без совпадений")
        search.press("Enter")
        expect(page.get_by_role("status")).to_have_text("Подходящих заявок не найдено")
        expect(table).to_have_count(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credentials", type=Path, help="private credentials.json printed by the local fixture")
    parser.add_argument("--screenshots", action="store_true", help="capture synthetic pages to .qa-visual")
    options = parser.parse_args()
    credentials = options.credentials.resolve()
    if credentials.parent.parent != ROOT or not credentials.parent.name.startswith(".qa-contract-"):
        parser.error("use credentials from the isolated backend fixture")
    ACCOUNTS = json.loads(credentials.read_text(encoding="utf-8"))
    if options.screenshots:
        SCREENSHOTS = ROOT / ".qa-visual"
        SCREENSHOTS.mkdir(exist_ok=True)
    unittest.main(argv=[__file__], verbosity=2)
