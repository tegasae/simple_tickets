"""Browser workflow checks against the loopback preview and a fresh --serve-i3 fixture."""

import argparse
import json
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:5174"
API = f"{ORIGIN}/api/admin"
HOTLINE = "Взято в работу на горячей линии"
ACCOUNTS = None


class BrowserI3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        playwright = cls.enterClassContext(sync_playwright())
        cls.browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        cls.addClassCleanup(cls.browser.close)

    def page_for(self, profile, scenario, *, timezone="UTC"):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id=timezone)
        self.addCleanup(context.close)
        errors = []
        self.addCleanup(lambda: self.assertEqual(errors, [], "Browser emitted uncaught JavaScript errors"))
        page = context.new_page()
        page.on("pageerror", lambda _: errors.append("uncaught page error"))
        ticket = ACCOUNTS["workflow"]["tickets"][scenario]
        page.goto(f"{ORIGIN}/tickets/{ticket['id']}")
        page.get_by_label("Логин", exact=True).fill(ACCOUNTS[profile]["username"])
        password = page.get_by_label("Пароль", exact=True)
        password.fill(ACCOUNTS[profile]["password"])
        with page.expect_response(f"{API}/admins/permissions") as permissions:
            password.press("Enter")
        self.assertEqual(permissions.value.status, 200)
        expect(page.get_by_role("heading", level=1, name=ticket["title"], exact=True)).to_be_visible()
        return page, f"{API}/tickets/{ticket['id']}"

    @staticmethod
    def panel(page):
        return page.get_by_role("region", name="Обработка заявки")

    def action(self, page, title):
        return self.panel(page).get_by_role("button", name=title, exact=True)

    def form(self, page, title):
        action = self.action(page, title)
        action.focus()
        action.press("Enter")
        form = self.panel(page).get_by_role("form", name=title)
        expect(form).to_be_visible()
        expect(form.get_by_role("heading", level=3, name=title)).to_be_focused()
        return form

    def patch_from(self, page, endpoint, submit):
        with page.expect_response(lambda response: response.url == endpoint and response.request.method == "PATCH") as received:
            submit.click()
        self.assertEqual(received.value.status, 200)
        return received.value.json()

    def confirm(self, page, form, endpoint):
        result = self.patch_from(page, endpoint, form.get_by_role("button", name="Подтвердить", exact=True))
        expect(self.panel(page).get_by_role("status").filter(has_text="Действие выполнено.")).to_be_visible()
        return result

    @staticmethod
    def expect_status(page, status, label):
        expect(page.locator(f'.badge[data-status="{status}"]')).to_have_text(label)

    def test_assigned_worker_finishes_and_reviewer_completes(self):
        dispatcher, endpoint = self.page_for("dispatcher", "lifecycle")
        self.expect_status(dispatcher, "created", "Создана")
        self.confirm(dispatcher, self.form(dispatcher, "Принять заявку"), endpoint + "/accept")
        self.expect_status(dispatcher, "accepted", "Принято")
        form = self.form(dispatcher, "Назначить исполнителя")
        field = form.get_by_role("combobox", name="Исполнитель", exact=True)
        worker_id = ACCOUNTS["workflow"]["actors"]["worker"]
        expect(field.get_by_role("option", name=f"Исполнитель И3 · № {worker_id}", exact=True)).to_be_attached()
        expect(field.get_by_role("option", name="Внешний Оператор", exact=False)).to_have_count(0)
        expect(field.get_by_role("option", name="Отключённый Исполнитель", exact=False)).to_have_count(0)
        expect(field.get_by_role("option", name="Диспетчер И3", exact=False)).to_have_count(0)
        field.select_option(str(worker_id))
        assigned = self.confirm(dispatcher, form, endpoint + "/executor")
        self.assertEqual(assigned["current_executor_id"], worker_id)
        self.expect_status(dispatcher, "assigned", "Назначено")

        peer, _ = self.page_for("peer_worker", "lifecycle")
        expect(self.action(peer, "Начать работу")).to_have_count(0)
        worker, _ = self.page_for("worker", "lifecycle")
        started = self.confirm(worker, self.form(worker, "Начать работу"), endpoint + "/start-work")
        self.assertIs(started["statuses"][-1]["work_is_remote"], False)
        self.expect_status(worker, "at_work", "В работе")
        self.confirm(worker, self.form(worker, "Приостановить работу"), endpoint + "/pause-work")
        self.expect_status(worker, "paused", "Работа приостановлена")
        self.confirm(worker, self.form(worker, "Продолжить работу"), endpoint + "/resume-work")
        self.expect_status(worker, "at_work", "В работе")
        submitted = self.confirm(worker, self.form(worker, "Завершить работу"), endpoint + "/finish-work")
        self.expect_status(worker, "ready_for_review", "Ожидает проверки")
        self.assertFalse(submitted["is_closed"])
        expect(self.action(worker, "Завершить проверку")).to_have_count(0)

        reviewer, _ = self.page_for("reviewer", "lifecycle")
        completed = self.confirm(reviewer, self.form(reviewer, "Завершить проверку"), endpoint + "/execute")
        self.expect_status(reviewer, "executed", "Выполнено")
        self.assertTrue(completed["is_closed"])
        self.assertEqual(completed["statuses"][-1]["actor_id"], ACCOUNTS["workflow"]["actors"]["reviewer"])

    def test_denied_actions_and_required_reason(self):
        reader, _ = self.page_for("reader", "reject")
        expect(self.action(reader, "Отклонить заявку")).to_have_count(0)
        expect(self.action(reader, "Принять заявку")).to_have_count(0)
        hotline, _ = self.page_for("hotline", "not_recommended")
        expect(self.action(hotline, HOTLINE)).to_have_count(0)
        expect(self.action(hotline, "Назначить исполнителя")).to_have_count(0)
        dispatcher, endpoint = self.page_for("dispatcher", "reject")
        form = self.form(dispatcher, "Отклонить заявку")
        reason = form.get_by_role("textbox", name="Причина", exact=True)
        writes = []
        dispatcher.on("request", lambda request: writes.append(request) if request.method == "PATCH" else None)
        form.get_by_role("button", name="Подтвердить", exact=True).click()
        expect(reason).to_be_focused()
        expect(reason).to_have_attribute("aria-invalid", "true")
        self.assertEqual(writes, [])
        reason.fill("Синтетическая причина проверки")
        rejected = self.confirm(dispatcher, form, endpoint + "/reject")
        self.assertEqual(rejected["statuses"][-1]["comment"], "Синтетическая причина проверки")
        self.assertEqual(len(writes), 1)

    def test_hotline_lost_response_is_reconciled_without_replay(self):
        page, endpoint = self.page_for("hotline", "hotline")
        page.get_by_role("link", name="Заявки", exact=True).click()
        page.get_by_role("link", name="Горячая линия", exact=True).click()
        ticket = ACCOUNTS["workflow"]["tickets"]["hotline"]
        row = page.get_by_role("row").filter(has_text=ticket["title"])
        expect(row.get_by_text("Рекомендовано для горячей линии", exact=True)).to_be_visible()
        unapproved = ACCOUNTS["workflow"]["tickets"]["not_recommended"]["title"]
        expect(page.get_by_role("row").filter(has_text=unapproved)).to_have_count(0)
        row.get_by_role("link", name=f"№ {ticket['id']}", exact=True).click()
        action = self.action(page, HOTLINE)
        expect(action).to_be_visible()
        expect(self.action(page, "Назначить исполнителя")).to_have_count(0)
        completed = []
        methods = []
        page.on("request", lambda request: methods.append((request.method, request.url)))

        def lose_patch_response(route):
            response = route.fetch()
            try:
                completed.append((response.status, route.request.post_data_json, response.json()))
            finally:
                response.dispose()
            route.abort()

        page.route(endpoint + "/start-remote-work", lose_patch_response)
        action.click()
        expect(self.panel(page).get_by_role("alert")).to_contain_text("Не удалось подтвердить результат")
        review = self.action(page, "Проверить состояние")
        expect(review).to_be_visible()
        with page.expect_response(lambda response: response.url == endpoint and response.request.method == "GET"):
            review.click()
        self.expect_status(page, "at_work", "В работе")
        expect(review).to_have_count(0)
        expect(self.panel(page).get_by_role("status").filter(
            has_text="В истории найден переход с указанными параметрами."
        )).to_be_visible()
        self.assertEqual(len(completed), 1)
        status, body, ticket = completed[0]
        self.assertEqual((status, body), (200, {}))
        self.assertEqual(ticket["current_executor_id"], ACCOUNTS["workflow"]["actors"]["hotline"])
        self.assertEqual([row["status"] for row in ticket["statuses"]], ["created", "accepted", "assigned", "at_work"])
        self.assertIs(ticket["statuses"][-1]["work_is_remote"], True)
        self.assertEqual([(method, url) for method, url in methods if method == "PATCH"],
                         [("PATCH", endpoint + "/start-remote-work")])

    def test_unchanged_or_unrelated_history_cannot_confirm_an_uncertain_write(self):
        page, endpoint = self.page_for("dispatcher", "unknown_unchanged")
        form = self.form(page, "Отложить заявку")
        reason = form.get_by_role("textbox", name="Причина", exact=True)
        reason.fill("Синтетическая причина отложенного перехода")
        requests = []

        def drop_request(route):
            requests.append(route.request.post_data_json)
            route.abort()

        page.route(endpoint + "/defer", drop_request)
        form.get_by_role("button", name="Подтвердить", exact=True).click()
        feedback = self.panel(page).get_by_role("alert").filter(has_text="Не удалось подтвердить результат")
        expect(feedback).to_be_visible()
        with page.expect_response(lambda response: response.url == endpoint and response.request.method == "GET"):
            self.action(page, "Проверить состояние").click()
        self.expect_status(page, "accepted", "Принято")
        expect(self.action(page, "Проверить состояние")).to_be_visible()
        expect(form.get_by_role("button", name="Подтвердить", exact=True)).to_be_disabled()
        expect(reason).to_have_value("Синтетическая причина отложенного перехода")

        login = page.request.post(f"{ORIGIN}/api/auth/admin/login", form=ACCOUNTS["dispatcher"])
        self.assertEqual(login.status, 200)
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        assigned = page.request.patch(endpoint + "/executor", headers=headers,
                                      data={"executor_id": ACCOUNTS["workflow"]["actors"]["worker"]})
        self.assertEqual(assigned.status, 200)
        with page.expect_response(lambda response: response.url == endpoint and response.request.method == "GET"):
            self.action(page, "Проверить состояние").click()
        self.expect_status(page, "assigned", "Назначено")
        expect(self.panel(page).get_by_role("alert").filter(
            has_text="В истории есть другое изменение."
        )).to_be_visible()
        expect(self.action(page, "Проверить состояние")).to_be_visible()
        expect(form.get_by_role("button", name="Подтвердить", exact=True)).to_be_disabled()
        expect(reason).to_have_value("Синтетическая причина отложенного перехода")
        self.assertEqual(requests, [{"comment": "Синтетическая причина отложенного перехода"}])

    def test_two_open_hotline_cards_do_not_overwrite_winner(self):
        first, endpoint = self.page_for("hotline", "hotline_race")
        second, _ = self.page_for("peer_hotline", "hotline_race")
        first_action = self.action(first, HOTLINE)
        second_action = self.action(second, HOTLINE)
        expect(second_action).to_be_visible()
        writes = []
        second.on("request", lambda request: writes.append(request.url) if request.method == "PATCH" else None)
        winner = self.patch_from(first, endpoint + "/start-remote-work", first_action)
        self.assertEqual(winner["current_executor_id"], ACCOUNTS["workflow"]["actors"]["hotline"])
        self.expect_status(first, "at_work", "В работе")
        second_action.click()
        expect(self.panel(second).get_by_role("alert")).to_contain_text("Состояние заявки изменилось")
        expect(self.action(second, "Проверить состояние")).to_be_visible()
        self.action(second, "Проверить состояние").click()
        self.expect_status(second, "at_work", "В работе")
        expect(second_action).to_have_count(0)
        self.assertEqual(writes, [], "A known stale card must not send a second workflow PATCH")

    def test_retrospective_duration_moves_assigned_ticket_to_review(self):
        page, endpoint = self.page_for("recorder", "retrospective")
        form = self.form(page, "Зарегистрировать выполненную работу")
        form.get_by_role("radio", name="Длительность", exact=True).check()
        form.get_by_role("spinbutton", name="Минуты", exact=True).fill("40")
        completed = self.confirm(page, form, endpoint + "/complete-work-retroactively")
        self.expect_status(page, "ready_for_review", "Ожидает проверки")
        work = completed["statuses"][-2]
        self.assertEqual((work["status"], work["duration"]), ("at_work", "PT40M"))
        self.assertEqual(work["actor_id"], ACCOUNTS["workflow"]["actors"]["recorder"])

    def test_retrospective_interval_rejects_clock_gap_and_preserves_entered_times(self):
        page, endpoint = self.page_for("recorder", "retrospective_interval", timezone="America/New_York")
        form = self.form(page, "Зарегистрировать выполненную работу")
        start = form.get_by_label("Начало")
        finish = form.get_by_label("Окончание")
        start.fill("2020-03-08T02:15")
        finish.fill("2020-03-08T03:40")
        writes = []
        page.on("request", lambda request: writes.append(request.url) if request.method == "PATCH" else None)
        form.get_by_role("button", name="Подтвердить", exact=True).click()
        expect(start).to_be_focused()
        expect(start).to_have_attribute("aria-invalid", "true")
        self.assertEqual(writes, [])
        start.fill("2020-03-08T01:45")
        completed = self.confirm(page, form, endpoint + "/complete-work-retroactively")
        self.expect_status(page, "ready_for_review", "Ожидает проверки")
        work = completed["statuses"][-2]
        self.assertEqual(work["actual_started_at"], "2020-03-08T06:45:00Z")
        self.assertEqual(work["actual_finished_at"], "2020-03-08T07:40:00Z")
        self.assertEqual(writes, [endpoint + "/complete-work-retroactively"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credentials", type=Path, help="private credentials file printed by --serve-i3")
    parser.add_argument("tests", nargs="*", help="optional unittest names")
    options = parser.parse_args()
    credentials = options.credentials.resolve()
    if (credentials.parent.parent != ROOT or not credentials.parent.name.startswith(".qa-contract-") or
            not (credentials.parent / "test.sqlite3").is_file() or credentials.name != "credentials.json"):
        parser.error("use the disposable loopback fixture credentials")
    ACCOUNTS = json.loads(credentials.read_text(encoding="utf-8"))
    if not isinstance(ACCOUNTS.get("workflow"), dict):
        parser.error("use credentials from --serve-i3")
    unittest.main(argv=[__file__, *options.tests], verbosity=2)
