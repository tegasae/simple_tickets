#!/usr/bin/env python3
"""Write editable Graphviz diagrams and validate their traced workflow transitions."""
import argparse
import json
import subprocess
from pathlib import Path

STYLE = '''
graph [fontname="DejaVu Sans", rankdir=TB, nodesep=0.23, ranksep=0.36, pad=0.16, bgcolor="white"]
node [fontname="DejaVu Sans", fontsize=11, shape=box, style="rounded,filled",
      fillcolor="#eff6f6", color="#458181", fontcolor="#123844", margin="0.11,0.075"]
edge [fontname="DejaVu Sans", fontsize=9, color="#345960", fontcolor="#17414a", arrowsize=0.68]
'''

def write_graph(output, name, body):
    source = output / (name + ".dot")
    source.write_text("digraph schedule {\n" + STYLE + body.strip() + "\n}\n", encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", str(source), "-o", str(output / (name + ".svg"))], check=True)

def edge_is_real(workflow, before, after):
    if after not in workflow[before]:
        raise ValueError(f"Unsupported status transition: {before} -> {after}")

def runtime_er(output, tables, name, keep, title):
    lines = [f'label={json.dumps(title, ensure_ascii=False)}; labelloc="t"; fontsize=13;',
             'node [shape=box, fontsize=10];']
    for table in sorted(keep):
        chosen = [column["name"] for column in tables[table]["columns"] if column["pk"]]
        label = table + ("\\nPK " + ", ".join(chosen) if chosen else "")
        lines.append(f'{table} [label="{label}"];')
    for table in sorted(keep):
        for foreign_key in tables[table]["foreign_keys"]:
            target = foreign_key["table"]
            if target in keep:
                lines.append(f'{table} -> {target} [label="{foreign_key["from"]}"];')
    write_graph(output, name, "\n".join(lines))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    workflows = json.loads((args.runtime / "workflows.json").read_text())
    tickets = workflows["ticket"]
    clients = workflows["ticket_user"]
    normal = ["created", "accepted", "assigned", "at_work", "ready_for_review"]
    for before, after in zip(normal, normal[1:]):
        edge_is_real(tickets, before, after)
    for before, after in [
        ("at_work", "paused"), ("paused", "at_work"),
        ("ready_for_review", "assigned"), ("ready_for_review", "accepted"),
        ("ready_for_review", "executed"), ("ready_for_review", "confirmed_by_user"),
        ("assigned", "suspended"), ("ready_for_review", "suspended"),
    ]:
        edge_is_real(tickets, before, after)
    for before, after in [
        ("created", "in_work"), ("in_work", "waiting_for_confirmation"),
        ("waiting_for_confirmation", "in_work"),
        ("waiting_for_confirmation", "confirmed_by_admin"),
        ("waiting_for_confirmation", "confirmed_by_user"),
        ("waiting_for_confirmation", "suspended"),
    ]:
        edge_is_real(clients, before, after)

    write_graph(output, "user-origins", '''
    user [label="Сотрудник клиента\\nподаёт обращение"]
    manager [label="Обычный сотрудник или менеджер\\nрегистрирует обращение за заявителя"]
    internal [label="Обычный сотрудник или менеджер\\nрегистрирует внутреннюю задачу"]
    pair [label="Две связанные карточки\\nВнутренняя заявка и обращение клиента"]
    only [label="Одна карточка\\nВнутренняя заявка"]
    {rank=same; user; manager; internal}
    {rank=same; pair; only}
    user -> pair
    manager -> pair
    internal -> only
    ''')

    write_graph(output, "user-ticket-life", '''
    node [fontsize=11]
    start [label="Новая заявка"]
    accepted [label="Принята"]
    assigned [label="Назначена"]
    work [label="Работа выполняется"]
    paused [label="Пауза"]
    review [label="На проверке"]
    done [label="Выполнена", fillcolor="#dff3e6"]
    clientdone [label="Подтверждена пользователем", fillcolor="#dff3e6"]
    start -> accepted [label="Приём"]
    accepted -> assigned [label="Назначение"]
    assigned -> work [label="Инженер начинает"]
    work -> paused [label="Перерыв"]
    paused -> work [label="Продолжение"]
    work -> review [label="Инженер передаёт результат"]
    review -> assigned [label="Назначить\\nна доработку", tailport=ne, headport=e, constraint=false]
    review -> accepted [label="Вернуть к обработке\\nи снять назначение", tailport=e, headport=e, constraint=false, style=dashed, color="#955a20", fontcolor="#77451a"]
    review -> done [label="Ведущий инженер или менеджер\\nс правом подтверждения"]
    review -> clientdone [label="Уполномоченный\\nсотрудник клиента"]
    {rank=same; work; paused}
    {rank=same; done; clientdone}
    ''')

    write_graph(output, "user-client-life", '''
    start [label="Создано"]
    work [label="В работе"]
    review [label="Ожидает подтверждения"]
    done [label="Подтверждено сотрудником", fillcolor="#dff3e6"]
    clientdone [label="Подтверждено пользователем", fillcolor="#dff3e6"]
    start -> work [label="Принята внутренняя заявка"]
    work -> review [label="Инженер передал результат"]
    review -> work [label="Вернули на доработку", constraint=false]
    review -> done [label="Сотрудник подтвердил"]
    review -> clientdone [label="Пользователь подтвердил"]
    {rank=same; done; clientdone}
    ''')

    write_graph(output, "user-hotline", '''
    request [label="Менеджер выставляет рекомендацию\\nи указывает отдел"]
    actor [label="Инженер с правом работы\\nна горячей линии проверяет заявку"]
    accepted [label="Принята и свободна"]
    assigned [label="Назначена этому инженеру"]
    blocked [label="Назначена другому\\nили нет рекомендации", fillcolor="#fff0d9"]
    claim [label="Назначает себя\\nв отделе заявки"]
    work [label="Работа выполняется удалённо"]
    review [label="На проверке"]
    message [label="Связаться с менеджером", fillcolor="#fff0d9"]
    request -> actor
    actor -> accepted
    actor -> assigned
    actor -> blocked
    accepted -> claim
    claim -> work
    assigned -> work
    blocked -> message
    work -> review
    {rank=same; accepted; assigned; blocked}
    ''')

    write_graph(output, "user-retrospective", '''
    assigned [label="Назначена"]
    register [label="Уполномоченный инженер вносит\\nинтервал или длительность"]
    work [label="Запись «Работа выполняется»"]
    review [label="Запись «На проверке»"]
    same [label="Назначение сохраняется.\\nАвтор записи может быть другим сотрудником.", shape=note]
    assigned -> register -> work -> review
    register -> same [style=dashed, arrowhead=none, label="пояснение"]
    ''')

    write_graph(output, "user-disable", '''
    request [label="Менеджер или руководитель отдела\\nограничивает доступ по полномочиям"]
    account [label="Только учётная запись"]
    client [label="Клиент, заявитель или контакт"]
    staff [label="Внутренний сотрудник"]
    accounts [label="Вход закрыт.\\nЗаявки сохраняют статус."]
    active [label="Работа выполняется"]
    open [label="Открыта вне выполнения"]
    blocked [label="Сначала завершить или снять\\nдействующие назначения", fillcolor="#fff0d9"]
    keep [label="Работа может продолжиться"]
    suspend [label="Приостановлена", fillcolor="#fff0d9"]
    request -> account -> accounts
    request -> client
    request -> staff
    staff -> blocked [label="при назначениях"]
    client -> active -> keep
    client -> open -> suspend
    {rank=same; account; client; staff}
    ''')

    write_graph(output, "tech-architecture", '''
    http [label="HTTP-клиент"]
    api [label="src.web.main.create_app()\\nFastAPI и маршруты"]
    auth [label="Проверка Bearer и доступности\\nget_current_admin / get_current_user"]
    req [label="Pydantic → DTO"]
    services [label="ApplicationServiceFactory\\nприкладной сервис и проверка права"]
    domain [label="Ticket / TicketUser / справочники\\nдоменные сервисы и политики"]
    uow [label="SQLiteUnitOfWork\\nодин connection на область запроса"]
    repositories [label="Repository → Gateway / Mapper"]
    db [label="SQLite"]
    http -> api -> auth -> req -> services
    services -> domain [label="вызов доменного действия"]
    services -> uow [label="выборка и запись"]
    uow -> repositories -> db
    {rank=same; domain; uow}
    ''')

    write_graph(output, "tech-execute-sequence", '''
    req [label="1. PATCH …/execute\\nпроверить действующего Admin"]
    perm [label="2. UoW + Authorizer\\nticket.executed?"]
    deny [label="403\\nдо изменения агрегатов", fillcolor="#fff0d9"]
    load [label="3. Загрузить Ticket и связанную TicketUser"]
    step [label="4. Домен\\nREADY_FOR_REVIEW → EXECUTED"]
    bad [label="400\\nоткат транзакции", fillcolor="#fff0d9"]
    sync [label="5. TicketSyncService\\nCONFIRMED_BY_ADMIN, если есть связанная карточка"]
    store [label="6. Репозитории\\nобе карточки, версии и история"]
    commit [label="7. COMMIT → 200", fillcolor="#dff3e6"]
    req -> perm
    perm -> deny [label="отказ"]
    perm -> load [label="разрешено"]
    load -> step
    step -> bad [label="переход запрещён"]
    step -> sync -> store -> commit
    {rank=same; step; bad}
    ''')

    write_graph(output, "tech-idempotency-sequence", '''
    req [label="1. HTTP: валидированное тело и необязательный ключ"]
    decision [label="2. В UoW найти запись по employee_id + key"]
    replay [label="Повторно проверить доступ, сравнить fingerprint"]
    fail [label="403 / 409\\nотказ доступа или конфликт", fillcolor="#fff0d9"]
    replayed [label="Сохранённый статус и тело", fillcolor="#dff3e6"]
    reserve [label="3. Зарезервировать ключ"]
    domain [label="4. Создать ресурс и результат в том же UoW"]
    rollback [label="Откат обеих записей", fillcolor="#fff0d9"]
    commit [label="5. COMMIT"]
    ttl [label="6. Ленивое обслуживание TTL\\nв отдельной короткой транзакции"]
    req -> decision
    decision -> replay [label="активный результат"]
    replay -> fail [label="отказ"]
    replay -> replayed [label="совпало"]
    decision -> reserve [label="свободный ключ"]
    reserve -> domain
    domain -> rollback [label="ошибка"]
    domain -> commit -> ttl
    {rank=same; reserve; replay}
    ''')

    write_graph(output, "tech-refresh-sequence", '''
    req [label="1. POST …/refresh"]
    find [label="2. SharedSessionAuthManager\\nнайти хеш и проверить срок и область"]
    auth [label="3. Проверить активность и привязку аккаунта"]
    deny [label="401; ротации нет", fillcolor="#fff0d9"]
    rotate [label="4. UoW: заменить запись refresh\\nс прежним абсолютным окончанием"]
    commit [label="5. COMMIT → новая пара токенов", fillcolor="#dff3e6"]
    req -> find
    find -> auth
    find -> deny [label="нет действующей записи"]
    auth -> deny [label="не прошёл проверку"]
    auth -> rotate -> commit
    ''')

    tables = json.loads((args.runtime / "tables.json").read_text())
    runtime_er(output, tables, "tech-er-tickets",
               {"tickets", "ticket_status_records", "ticket_comments", "user_tickets",
                "user_tickets_status_record", "user_tickets_comment", "employees", "clients", "departments"},
               "Карточки и история: стрелка от внешнего ключа к цели")
    runtime_er(output, tables, "tech-er-access",
               {"employees", "admins", "users", "departments", "clients", "accounts", "roles",
                "admins_roles", "users_roles", "auth_refresh_sessions", "creation_results"},
               "Учётные данные и доступ: физические внешние ключи")

if __name__ == "__main__":
    main()
