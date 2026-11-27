"""Measure browser projection against candidate dist and isolated synthetic HTTP responses.

From frontend v3, run `python -B tests/browser_performance.py`. The optional
`--dist` selects a built candidate without modifying it.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from math import ceil
from pathlib import Path
from statistics import median
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


VIEWPORT = {"width": 1440, "height": 900}
FIND_TERM = "Синтетическая сеть"
SYNTHETIC_ACCESS = "header.eyJzdWIiOiIxNyIsInN1YmplY3RfdHlwZSI6ImFkbWluIn0.signature"
HISTORIES = (
    ("created",),
    ("created_from_request_user", "accepted"),
    ("created_from_ticket_user", "accepted", "assigned"),
    ("created", "accepted", "assigned", "at_work"),
    ("created", "accepted", "assigned", "at_work", "paused"),
    ("created_from_request_user", "accepted", "assigned", "at_work", "ready_for_review"),
    ("created", "accepted", "deferred"),
)


def scenario(count):
    start = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
    tickets = []
    for ticket_id in range(1, count + 1):
        initial_date = start + timedelta(minutes=ticket_id)
        history = HISTORIES[ticket_id % len(HISTORIES)]
        executor = ticket_id % 27 + 101 if "assigned" in history else 0
        requester = ticket_id % 317 + 1001 if history[0] != "created" else 0
        statuses = [
            {
                "id": ticket_id * 100 + sequence,
                "status": status,
                "actor_id": 17 if status not in {"at_work", "paused", "ready_for_review"} else executor,
                "executor_id": executor if status == "assigned" else 0,
                "date_created": (initial_date + timedelta(minutes=sequence)).isoformat(),
                "actual_started_at": None,
                "actual_finished_at": None,
                "duration": "PT0S",
                "work_is_remote": ticket_id % 2 == 0 if status == "at_work" else None,
                "comment": "Синтетическое событие для замера." if sequence % 2 == 0 else "",
            }
            for sequence, status in enumerate(history)
        ]
        comments = [
            {
                "id": ticket_id * 10 + sequence,
                "actor_id": 17,
                "comment": "Синтетический комментарий. Состояние проверено на тестовых данных.",
                "date_created": (initial_date + timedelta(minutes=sequence + 10)).isoformat(),
            }
            for sequence in range(ticket_id % 5)
        ]
        title = FIND_TERM if ticket_id % 10 == 0 else "Синтетическая проверка рабочего места"
        tickets.append({
            "ticket_id": ticket_id,
            "client_id": ticket_id % 137 + 1,
            "user_id": requester,
            "contact_user_id": requester,
            "user_ticket_id": ticket_id + 30000 if requester else 0,
            "department_id": ticket_id % 9 + 1,
            "text_of_ticket": f"{title} SYN-{ticket_id:06d}",
            "description": (
                "Запись создана для измерения времени обработки списка. "
                "История и комментарии служат синтетической нагрузкой. "
                "Исходные рабочие данные в сценарии отсутствуют."
            ),
            "date_created": initial_date.isoformat(),
            "date_finished": None,
            "planned_at": None,
            "remote_work_recommended": ticket_id % 5 == 0,
            "urgency": ["normal", "normal", "urgent", "maintenance"][ticket_id % 4],
            "current_executor_id": executor,
            "last_executor_id": executor,
            "is_closed": False,
            "time_spent": 0,
            "statuses": statuses,
            "comments": comments,
        })
    return tickets


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


@contextmanager
def fixture(directory, tickets):
    encoded_list = encode(tickets)
    by_id = {str(ticket["ticket_id"]): encode(ticket) for ticket in tickets}
    tokens = encode({
        "access_token": SYNTHETIC_ACCESS,
        "refresh_token": "loopback-fixture",
        "token_type": "bearer",
        "expires_in": 300,
        "scope": "",
    })

    class Handler(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        disable_nagle_algorithm = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, *_args):
            return

        def send_json(self, body, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self):
            if length := self.headers.get("Content-Length"):
                self.rfile.read(int(length))
            if self.path in ("/api/auth/admin/login", "/api/auth/admin/refresh"):
                self.send_json(tokens)
            else:
                self.send_json(b"{}", status=404)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path.startswith("/api/"):
                if self.headers.get("Authorization") != f"Bearer {SYNTHETIC_ACCESS}":
                    self.send_json(b"{}", status=401)
                elif path == "/api/admin/admins/permissions":
                    self.send_json(b'{"permissions":["ticket.view"]}')
                elif path in ("/api/admin/tickets/", "/api/admin/tickets/open"):
                    self.send_json(encoded_list)
                else:
                    ticket = by_id.get(path.removeprefix("/api/admin/tickets/"))
                    self.send_json(ticket if ticket is not None else b"{}", 200 if ticket is not None else 404)
                return
            if path in ("/", "/login", "/tickets") or path.startswith("/tickets/"):
                self.path = "/index.html"
            super().do_GET()

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", len(encoded_list)
        finally:
            server.shutdown()
            thread.join()


CLICK_AND_MEASURE = r"""async (trigger, options) => {
    const previousTable = document.querySelector("table tbody");
    const initial = performance.now();
    const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
    const resource = () => performance.getEntriesByType("resource").find(entry =>
        entry.startTime >= initial && new URL(entry.name).pathname === options.resource);
    const rows = () => [...document.querySelectorAll("table tbody tr")];
    function committed() {
        if (options.kind === "queue") {
            return (document.querySelector("table tbody") !== previousTable &&
                rows().length === options.rows && Boolean(resource()));
        }
        if (options.kind === "search") {
            return rows().length === options.rows &&
                document.querySelector(".search-value")?.textContent.includes(options.term) &&
                rows().every(row => row.cells[1].textContent.includes(options.term));
        }
        return document.querySelector(".ticket-detail h1")?.textContent === options.title &&
            Boolean(resource());
    }
    let notify;
    let reject;
    const ready = new Promise((resolve, fail) => {
        notify = () => { if (committed()) resolve(performance.now()); };
        reject = fail;
    });
    const mutation = new MutationObserver(notify);
    const resources = new PerformanceObserver(notify);
    mutation.observe(document.body, { childList: true, characterData: true, subtree: true });
    resources.observe({ entryTypes: ["resource"] });
    const timer = setTimeout(() => reject(Error("No committed " + options.kind + " state")), 15000);
    trigger.click();
    notify();
    let seen;
    try {
        seen = await ready;
    } finally {
        clearTimeout(timer);
        mutation.disconnect();
        resources.disconnect();
    }
    const read = options.resource ? resource() : null;
    await frame();
    await frame();
    const painted = performance.now();
    return {
        rows: rows().length,
        commit_ms: seen - initial,
        two_frames_ms: painted - initial,
        resource_ms: read ? read.responseEnd - read.startTime : null,
        resource_to_commit_ms: read ? seen - read.responseEnd : null,
        resource_to_two_frames_ms: read ? painted - read.responseEnd : null,
        encoded_body_bytes: read ? read.encodedBodySize : null,
        ticket_reads: performance.getEntriesByType("resource").filter(entry =>
            entry.startTime >= initial && new URL(entry.name).pathname.startsWith("/api/admin/tickets")).length,
    };
}"""


def do_measure(locator, kind, **options):
    return locator.evaluate(CLICK_AND_MEASURE, {"kind": kind, **options})


def metrics(samples):
    durations = {}
    for key in samples[0]:
        values = sorted(sample[key] for sample in samples if sample[key] is not None)
        if not values:
            continue
        if key.endswith("_ms"):
            durations[key] = {
                "p50": round(median(values), 1),
                "p95": round(values[ceil(len(values) * 0.95) - 1], 1),
            }
        else:
            durations[key] = {"min": min(values), "max": max(values)}
    return durations


def run_tier(browser, directory, count, repetitions, warmups):
    tickets = scenario(count)
    with fixture(directory, tickets) as (origin, encoded_size):
        context = browser.new_context(viewport=VIEWPORT, locale="ru-RU")
        try:
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.add_init_script("performance.setResourceTimingBufferSize(1500)")
            page.goto(origin + "/tickets?queue=open")
            page.get_by_label("Логин", exact=True).fill("synthetic-benchmark")
            page.get_by_label("Пароль", exact=True).fill("synthetic-benchmark")
            first = do_measure(page.get_by_role("button", name="Войти", exact=True),
                               "queue", rows=25, resource="/api/admin/tickets/open")

            loads = []
            for sequence in range(repetitions + warmups):
                select_open = sequence % 2 == 1
                name = "Открытые" if select_open else "Все"
                path = "/api/admin/tickets/open" if select_open else "/api/admin/tickets/"
                data = do_measure(page.get_by_role("link", name=name, exact=True), "queue", rows=25, resource=path)
                if sequence >= warmups:
                    loads.append(data)

            searches = []
            expected_rows = min(25, count // 10)
            for sequence in range(repetitions + warmups):
                page.get_by_role("searchbox", name="Поиск заявок").fill(FIND_TERM)
                data = do_measure(page.get_by_role("button", name="Найти", exact=True),
                                  "search", rows=expected_rows, term=FIND_TERM)
                if sequence >= warmups:
                    searches.append(data)
                page.locator(".active-filters").get_by_role("button", name="Сбросить", exact=True).click()
                expect(page.locator(".active-filters")).to_have_count(0)

            # The two cards are opened before measurement. The current app still
            # reads the detail on each switch, so record that separately.
            for sequence, ticket in enumerate(tickets[-2:]):
                page.locator(f"#ticket-link-{ticket['ticket_id']}").click()
                expect(page.locator(".ticket-detail h1")).to_have_text(ticket["text_of_ticket"])
                if sequence == 0:
                    page.get_by_role("link", name="К списку заявок", exact=True).click()

            switches = []
            details = tickets[-2:]
            for sequence in range(repetitions + warmups):
                ticket = details[sequence % 2]
                ticket_id = ticket["ticket_id"]
                data = do_measure(page.locator(f"#work-tab-{ticket_id}"), "ticket",
                                  title=ticket["text_of_ticket"], resource=f"/api/admin/tickets/{ticket_id}")
                if sequence >= warmups:
                    switches.append(data)

            if errors:
                raise RuntimeError("Unexpected browser errors: " + repr(errors))
            return {
                "tickets": count,
                "encoded_queue_bytes": encoded_size,
                "mean_history_records": round(sum(len(ticket["statuses"]) for ticket in tickets) / count, 2),
                "mean_comments": round(sum(len(ticket["comments"]) for ticket in tickets) / count, 2),
                "first_login_and_queue_ms": first["two_frames_ms"],
                "queue_reload": metrics(loads),
                "search": metrics(searches),
                "work_tab_switch": metrics(switches),
            }
        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    parser.add_argument("--chromium", type=Path, default=Path("/usr/bin/chromium"))
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--counts", nargs="+", type=int, default=[100, 5000])
    args = parser.parse_args()
    if not (args.dist / "index.html").is_file():
        parser.error("build the v3 candidate before measuring")
    if args.repetitions < 1 or args.warmups < 0 or any(count < 25 for count in args.counts):
        parser.error("use positive repetitions, nonnegative warmups and at least 25 tickets per tier")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True)
        try:
            measurements = [
                run_tier(browser, args.dist, count, args.repetitions, args.warmups) for count in args.counts
            ]
            print(json.dumps({
                "chromium": browser.version,
                "viewport": VIEWPORT,
                "samples_per_metric": args.repetitions,
                "discarded_warmup_samples": args.warmups,
                "tiers": measurements,
            }, indent=2))
        finally:
            browser.close()


if __name__ == "__main__":
    main()
