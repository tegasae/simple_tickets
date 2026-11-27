"""TC-018/019 on one disposable copy of an already built production frontend.

Start the synthetic `backend_contract.py --serve` fixture first. The test
server hosts the copied assets on loopback and forwards same-origin API calls
to that fixture. The test updates JSON files there and never rebuilds assets.
"""

import argparse
from contextlib import contextmanager, suppress
import hashlib
import http.client
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
from tempfile import NamedTemporaryFile, TemporaryDirectory
from threading import Thread
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
THEMES = Path("config/themes.json")
LANGUAGES = Path("config/locales.json")
RUSSIAN = Path("config/locales/ru-RU.json")
ENGLISH = Path("config/locales/en-US.json")
THEME_IDS = {"classic", "onec", "futuristic", "barbie"}
THEME_LABEL = "Тема оформления"
LANGUAGE_LABEL = "Язык интерфейса"
TICKET_TITLE = "Проверка печати"
TICKET_PATH = "/tickets/1"
DIST = None
ACCOUNTS = None


class FixtureHandler(SimpleHTTPRequestHandler):
    def handle(self):
        # A normal page reload can cancel an in-flight detail request.
        with suppress(BrokenPipeError, ConnectionResetError):
            super().handle()

    def log_message(self, _format, *_args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            self.forward_api()
            return
        if path == "/tickets" or re.fullmatch(r"/tickets/[1-9]\d*", path):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if urlsplit(self.path).path.startswith("/api/auth/admin/"):
            self.forward_api()
        else:
            self.send_error(405)

    def forward_api(self):
        headers = {key: self.headers[key] for key in ("Accept", "Authorization", "Content-Type")
                   if key in self.headers}
        size = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(size) if size else None
        upstream = http.client.HTTPConnection("127.0.0.1", 18080, timeout=20)
        try:
            upstream.request(self.command, self.path.removeprefix("/api"), body=body, headers=headers)
            response = upstream.getresponse()
            contents = response.read()
        except (OSError, http.client.HTTPException):
            self.send_error(502)
            return
        finally:
            upstream.close()
        self.send_response(response.status)
        if response.getheader("Content-Type"):
            self.send_header("Content-Type", response.getheader("Content-Type"))
        self.send_header("Content-Length", str(len(contents)))
        self.end_headers()
        self.wfile.write(contents)


@contextmanager
def serve(directory):
    def handler(*args, **kwargs):
        return FixtureHandler(*args, directory=str(directory), **kwargs)

    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def contents_hash(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.suffix in {".js", ".css"}
    }


def replace_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        swap = Path(temporary.name)
    try:
        swap.replace(path)
    finally:
        swap.unlink(missing_ok=True)


def contrast_ratio(first, second):
    def luminance(rgb):
        red, green, blue = (int(component) / 255 for component in re.findall(r"\d+", rgb))
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                  for value in (red, green, blue)]
        return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


class BrowserAppearance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace = Path(cls.enterClassContext(TemporaryDirectory(prefix="simple-tickets-appearance-")))
        cls.copy = workspace / "dist"
        shutil.copytree(DIST, cls.copy)
        cls.hashes = contents_hash(cls.copy)
        if not {".js", ".css"}.issubset({Path(name).suffix for name in cls.hashes}):
            raise AssertionError("the production copy has no built JavaScript or CSS")
        cls.origin = cls.enterClassContext(serve(cls.copy))
        playwright = cls.enterClassContext(sync_playwright())
        cls.browser = playwright.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True,
            args=["--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"],
        )
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        original = {relative: (self.copy / relative).read_bytes() if (self.copy / relative).exists() else None
                    for relative in (THEMES, LANGUAGES, RUSSIAN, ENGLISH)}

        def restore():
            for relative, content in original.items():
                path = self.copy / relative
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    replace_file(path, content)

        self.addCleanup(restore)
        self.addCleanup(lambda: self.assertEqual(contents_hash(self.copy), self.hashes, "deployed JS or CSS changed"))

    def config(self, path):
        return json.loads((self.copy / path).read_bytes())

    def publish(self, path, payload):
        replace_file(self.copy / path, json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"))

    def page(self, path=TICKET_PATH):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id="UTC")
        self.addCleanup(context.close)
        errors = []
        cross_origin = []
        config_credentials = []
        self.addCleanup(lambda: self.assertEqual(errors, [], "Chromium emitted uncaught JavaScript errors"))
        self.addCleanup(lambda: self.assertEqual(cross_origin, [], "page tried to load cross-origin content"))
        self.addCleanup(lambda: self.assertEqual(config_credentials, [], "config request carried API credentials"))
        page = context.new_page()
        page.on("pageerror", lambda _: errors.append("uncaught page error"))

        def watch_origin(request):
            url = urlsplit(request.url)
            if (url.scheme, url.netloc) != ("http", urlsplit(self.origin).netloc):
                cross_origin.append(f"{url.scheme}://{url.netloc}")
            elif url.path.startswith("/config/") and request.header_value("authorization"):
                config_credentials.append(url.path)

        # Observe requests without Playwright routing, which disables Chromium's HTTP cache.
        context.on("request", watch_origin)
        page.goto(self.origin + path)
        return page

    def login(self, page, button="Войти"):
        account = ACCOUNTS["writer"]
        page.get_by_label("Логин", exact=True).fill(account["username"])
        page.get_by_label("Пароль", exact=True).fill(account["password"])
        with page.expect_response(self.origin + "/api/auth/admin/login") as auth:
            with page.expect_response(self.origin + "/api/admin" + TICKET_PATH) as ticket:
                page.get_by_role("button", name=button, exact=True).click()
        self.assertEqual(auth.value.status, 200)
        self.assertEqual(ticket.value.status, 200)
        expect(page.get_by_role("heading", level=1, name=TICKET_TITLE, exact=True)).to_be_visible()
        return ticket.value.json()

    @staticmethod
    def select(page, label):
        return page.get_by_role("combobox", name=label, exact=True)

    @staticmethod
    def options(control):
        return control.locator("option").evaluate_all("(options) => options.map((option) => option.value)")

    @staticmethod
    def creation_date(page, label):
        return page.locator("dt").filter(has_text=re.compile(f"^{re.escape(label)}$")).locator("xpath=following-sibling::dd[1]")

    @staticmethod
    def localized_date(page, locale, value):
        return page.evaluate(
            """([language, time]) => new Intl.DateTimeFormat(language, {
                year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"
            }).format(new Date(time))""",
            [locale, value],
        )

    def test_published_theme_selects_with_keyboard_and_falls_back_on_bad_catalogs(self):
        page = self.page()
        self.login(page)
        theme = self.select(page, THEME_LABEL)
        body = page.locator("body")

        def expect_palette(background):
            expect(body).to_have_css("background-color", background)
            foreground = body.evaluate("(element) => getComputedStyle(element).color")
            self.assertGreaterEqual(contrast_ratio(foreground, background), 4.5)

        expect(theme).to_have_value("classic")
        self.assertEqual(set(self.options(theme)), THEME_IDS)
        for identifier, background in (
            ("onec", "rgb(236, 233, 220)"),
            ("futuristic", "rgb(5, 7, 19)"),
            ("barbie", "rgb(255, 240, 248)"),
            ("classic", "rgb(244, 246, 248)"),
        ):
            with self.subTest(theme=identifier):
                theme.select_option(identifier)
                expect_palette(background)

        baseline = self.config(THEMES)
        classic = next(item for item in baseline["themes"] if item["id"] == "classic")
        published = {**baseline, "themes": [*baseline["themes"], {
            "id": "qa-sky", "label": "Небо QA", "tokens": {**classic["tokens"], "--bg": "#e2f1f8"},
        }]}
        self.publish(THEMES, published)
        page.reload()
        expect(theme.locator('option[value="qa-sky"]')).to_have_count(1)
        self.assertEqual(set(self.options(theme)), THEME_IDS | {"qa-sky"})
        page.get_by_role("button", name="Редактировать заявку", exact=True).click()
        description = page.get_by_role("form", name="Изменение заявки").get_by_label("Описание", exact=True)
        description.fill("Черновик остаётся при переключении")
        theme.focus()
        theme.press("End")
        expect(theme).to_have_value("qa-sky")
        expect(theme).to_be_focused()
        outline = theme.evaluate("(control) => getComputedStyle(control).outlineStyle")
        self.assertNotIn(outline, {"none", "hidden"})
        expect(description).to_have_value("Черновик остаётся при переключении")
        expect_palette("rgb(226, 241, 248)")
        page.reload()
        expect(theme).to_have_value("qa-sky")
        expect(body).to_have_css("background-color", "rgb(226, 241, 248)")

        def expect_baseline():
            expect(theme).to_have_value("classic")
            self.assertEqual(set(self.options(theme)), THEME_IDS)
            expect(body).to_have_css("background-color", "rgb(244, 246, 248)")

        self.publish(THEMES, baseline)
        page.reload()
        expect_baseline()
        replace_file(self.copy / THEMES, b"{")
        page.reload()
        expect(theme).to_have_count(0)
        expect(body).to_have_css("background-color", "rgb(244, 246, 248)")
        (self.copy / THEMES).unlink()
        page.reload()
        expect(theme).to_have_count(0)
        expect(body).to_have_css("background-color", "rgb(244, 246, 248)")

    def test_published_texts_and_new_locale_apply_on_unchanged_assets(self):
        page = self.page()
        root = page.locator("html")
        expect(page.get_by_role("button", name="Войти", exact=True)).to_be_visible()
        expect(self.select(page, LANGUAGE_LABEL)).to_have_count(0)
        expect(root).to_have_attribute("lang", "ru-RU")

        russian = self.config(RUSSIAN)
        caption = "Войти в рабочее место"
        inert = "<strong>Локальная подсказка</strong>"
        russian["messages"].update({
            "login.submit": caption,
            "login.showPassword": inert,
            "work.closeTab": "Закрыть карточку № {id}",
            "work.closeTitle": "Проверить черновик заявки № {id}",
        })
        self.publish(RUSSIAN, russian)
        page.reload()
        expect(self.select(page, LANGUAGE_LABEL)).to_have_count(0)
        toggle = page.get_by_role("button", name=inert, exact=True)
        expect(toggle).to_be_visible()
        expect(toggle.locator("strong")).to_have_count(0)
        toggle.click()
        expect(page.get_by_label("Пароль", exact=True)).to_have_attribute("type", "text")
        ticket = self.login(page, caption)
        created = ticket["statuses"][0]["date_created"]
        ru_date = self.localized_date(page, "ru-RU", created)
        expect(self.creation_date(page, "Дата создания")).to_have_text(ru_date)

        edit = page.get_by_role("form", name="Изменение заявки")
        page.get_by_role("button", name="Редактировать заявку", exact=True).click()
        description = edit.get_by_label("Описание", exact=True)
        description.fill("Черновик для проверки подписей")
        close = page.get_by_role("button", name="Закрыть карточку № 1", exact=True)
        close.focus()
        close.press("Enter")
        dialog = page.get_by_role("dialog", name="Проверить черновик заявки № 1")
        expect(dialog).to_be_visible()
        keep = dialog.get_by_role("button", name="Продолжить редактирование", exact=True)
        expect(keep).to_be_focused()
        keep.press("Escape")
        expect(dialog).to_have_count(0)
        expect(description).to_have_value("Черновик для проверки подписей")

        manifest = self.config(LANGUAGES)
        manifest["languages"].append({"id": "en-US", "label": "English (US)"})
        self.publish(ENGLISH, {"version": 1, "language": "en-US", "messages": {
            "ticket.createdAt": "Created on",
            "workflow.reasonRequired": "Enter a reason.",
            "work.closeTab": "Invalid placeholder {unexpected}",
        }})
        self.publish(LANGUAGES, manifest)
        page.reload()
        language = self.select(page, LANGUAGE_LABEL)
        expect(language).to_have_value("ru-RU")
        self.assertEqual(set(self.options(language)), {"ru-RU", "en-US"})
        page.get_by_role("button", name="Отложить заявку", exact=True).click()
        defer = page.get_by_role("form", name="Отложить заявку")
        reason = defer.get_by_role("textbox", name="Причина", exact=True)
        defer.get_by_role("button", name="Подтвердить", exact=True).click()
        problem = defer.locator(".field-error")
        expect(problem).to_have_text("Укажите причину.")
        expect(reason).to_be_focused()
        language.focus()
        language.press("End")
        expect(root).to_have_attribute("lang", "en-US")
        expect(language).to_be_focused()
        expect(problem).to_have_text("Enter a reason.")
        expect(reason).to_have_attribute("aria-invalid", "true")
        en_date = self.localized_date(page, "en-US", created)
        self.assertNotEqual(ru_date, en_date)
        expect(self.creation_date(page, "Created on")).to_have_text(en_date)
        expect(page.get_by_role("button", name="Закрыть заявку № 1", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="Описание", exact=True)).to_be_visible()
        page.reload()
        expect(root).to_have_attribute("lang", "en-US")
        expect(language).to_have_value("en-US")
        expect(self.creation_date(page, "Created on")).to_have_text(en_date)

        replace_file(self.copy / ENGLISH, b"{")
        page.reload()
        expect(root).to_have_attribute("lang", "ru-RU")
        expect(self.creation_date(page, "Дата создания")).to_have_text(ru_date)
        (self.copy / ENGLISH).unlink()
        page.reload()
        expect(root).to_have_attribute("lang", "ru-RU")
        expect(self.creation_date(page, "Дата создания")).to_have_text(ru_date)

        replace_file(self.copy / LANGUAGES, b'{"version":99,"languages":[]}')
        page.reload()
        expect(root).to_have_attribute("lang", "ru-RU")
        expect(language).to_have_count(0)
        expect(page.get_by_role("heading", level=1, name=TICKET_TITLE, exact=True)).to_be_visible()

        remote_id = "https://example.invalid/runtime-locale"
        self.publish(LANGUAGES, {**manifest, "defaultLanguage": remote_id,
                                "languages": [*manifest["languages"], {"id": remote_id, "label": "External locale"}]})
        page.reload()
        expect(root).to_have_attribute("lang", "ru-RU")
        expect(page.get_by_role("option", name="External locale", exact=True)).to_have_count(0)

        (self.copy / LANGUAGES).unlink()
        degraded_login = self.page()
        expect(self.select(degraded_login, LANGUAGE_LABEL)).to_have_count(0)
        expect(degraded_login.locator("html")).to_have_attribute("lang", "ru-RU")
        self.login(degraded_login)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("credentials", type=Path, help="private credentials file printed by backend_contract.py --serve")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist", help="production frontend assets to copy")
    options = parser.parse_args()
    credentials = options.credentials.resolve()
    if (credentials.parent.parent != ROOT or not credentials.parent.name.startswith(".qa-contract-") or
            not (credentials.parent / "test.sqlite3").is_file() or credentials.name != "credentials.json"):
        parser.error("use credentials from the disposable loopback backend fixture")
    DIST = options.dist.resolve()
    if not (DIST / "index.html").is_file():
        parser.error("supply an existing production build directory")
    ACCOUNTS = json.loads(credentials.read_text(encoding="utf-8"))
    unittest.main(argv=[__file__], verbosity=2)
