#!/usr/bin/env python3
"""Build the API, source and schema reference from a frozen checkout and runtime facts."""
import argparse
import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

HTTP = {"get", "post", "put", "patch", "delete", "head", "options"}
SERVICE_FILES = {
    "/admin/admins": "admin_service",
    "/admin/clients": "client_service",
    "/admin/departments": "department_service",
    "/admin/roles": "role_service",
    "/admin/tickets": "ticket_service",
    "/admin/users": "user_service",
    "/user/tickets": "ticket_user_service",
}
SERVICE_POLICY = {
    "ticket_service": "Внутренняя карточка выбирается по ID. У операций работы действуют проверки исполнителя, состояния и рекомендации из BR-007–BR-013.",
    "ticket_user_service": "Проверяются принадлежность клиенту и область «владелец» или «все заявки клиента» в зависимости от действия; см. BR-001 и BR-018.",
    "admin_service": "Внутренние сотрудники. Для смены отдела, отключения или удаления проверяются текущие назначения и ссылки.",
    "client_service": "Справочник клиентов. Решения об активности и удалении учитывают зависимые данные.",
    "user_service": "Сотрудники клиента. При создании и включении проверяется клиент. Назначение ролей относится к пользовательскому контуру.",
    "department_service": "Справочник отделов. При отключении и удалении учитываются сотрудники и заявки.",
    "role_service": "Административные и пользовательские роли раздельны. Создание и управление ролью выполняются в соответствующем контуре.",
}
SENSITIVE = re.compile(r"password|secret|credential|auth.token|refresh_token|access_token", re.I)

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, text):
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def inline(text):
    return "`" + str(text).replace("`", "") + "`"

def tbl(text):
    return str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "")

class Source:
    def __init__(self, root, revision):
        self.root = root
        self.revision = revision
        self.trees = {}
        self.nodes = {}
        self.imports = {}
        self.tests = {}
        roots = [root / folder for folder in ("src", "utils", "scripts")]
        files = [file for folder in roots if folder.is_dir() for file in folder.rglob("*.py")]
        files.extend(root / filename for filename in ("main.py", "config.py", "models.py")
                     if (root / filename).is_file())
        for file in sorted(files):
            name = file.relative_to(root).as_posix()
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=name)
            self.trees[name] = tree
            self.nodes[name] = list(self.symbols(tree.body))
            self.imports[name] = self.module_imports(tree, name)
        for file in sorted((root / "tests").glob("test_*.py")):
            name = file.relative_to(root).as_posix()
            self.tests[name] = self.module_imports(ast.parse(file.read_text()), name)

    @staticmethod
    def symbols(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                yield prefix + node.name, node
                yield from Source.symbols(node.body, prefix=prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield prefix + node.name, node

    @staticmethod
    def module_imports(tree, path):
        package = path.rsplit("/", 1)[0].split("/") if "/" in path else []
        result = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                base = package[:len(package) - node.level + 1] if node.level else []
                if node.module:
                    base += node.module.split(".")
                module = ".".join(base)
                if module:
                    result.add(module)
                if not node.module:
                    result.update(".".join([*base, alias.name]) for alias in node.names)
        return sorted(result)

    def link(self, path, node=None, label=None, line=None):
        fragment = f"#L{line}" if line else ""
        if node:
            start, end = node.lineno, getattr(node, "end_lineno", node.lineno)
            fragment = f"#L{start}-L{end}" if end != start else f"#L{start}"
        return f"[{label or path}](https://github.com/tegasae/simple_tickets/blob/{self.revision}/{quote(path)}{fragment})"

    def methods(self, file, role_wrapper=None):
        return {name.split(".")[-1]: (name, node) for name, node in self.nodes.get(file, [])
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and (role_wrapper is None or name.split(".")[0] in {role_wrapper, "RoleApplicationService"})}

    @staticmethod
    def attributes(node):
        body = ast.Module(body=node.body, type_ignores=[]) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else node
        return {call.func.attr for call in ast.walk(body) if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)}

    @staticmethod
    def action_errors(node):
        names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc is not None:
                value = child.exc.func if isinstance(child.exc, ast.Call) else child.exc
                if isinstance(value, (ast.Name, ast.Attribute)):
                    names.add(ast.unparse(value))
        return sorted(names)

    def trace(self, router, node, target, role_realm=None):
        wrapper = {"admin": "AdminRoleApplicationService", "user": "UserRoleApplicationService"}.get(role_realm)
        methods = self.methods(target, wrapper)
        matching = self.attributes(node) & methods.keys()
        wrappers = {name.split(".")[0] for name, item in self.nodes.get(router, [])
                    if isinstance(item, ast.ClassDef) and name.endswith("Operation")}
        for called in ast.walk(node):
            if isinstance(called, ast.Call) and isinstance(called.func, ast.Name) and called.func.id in wrappers:
                for name, item in self.nodes.get(router, []):
                    if name.startswith(called.func.id + ".") and isinstance(item, ast.FunctionDef):
                        matching |= self.attributes(item) & methods.keys()
        matching -= {"__init__", "get", "_save_and_to_dto"}
        visible = []
        fields = set()
        permissions = set()
        errors = set(self.action_errors(node))
        queue = [(name, 0) for name in sorted(matching)]
        visited = set()
        while queue:
            name, depth = queue.pop(0)
            if name in visited:
                continue
            visited.add(name)
            qualified, method = methods[name]
            if depth == 0 or name.startswith(("require_", "_require", "_check_actor")):
                visible.append(self.link(target, method, qualified))
            for child in ast.walk(method):
                if not isinstance(child, ast.Attribute):
                    continue
                value = child.value
                if isinstance(value, ast.Name) and value.id in {"AdminPermission", "UserPermission"}:
                    permissions.add(ast.unparse(child))
                if isinstance(value, ast.Name) and (value.id.endswith("dto") or value.id.startswith("dto_")):
                    fields.add(child.attr)
            errors.update(self.action_errors(method))
            if depth < 2:
                queue.extend((s, depth + 1) for s in sorted(self.attributes(method) & methods.keys())
                             if s.startswith(("require_", "_require", "_check_actor")))
        if role_realm and matching:
            permissions = {"AdminPermission.ROLE_ASSIGN" if role_realm == "admin"
                           else "AdminPermission.ROLE_USER_ASSIGN"}
        return visible, sorted(permissions), sorted(fields), sorted(errors)

    def routes(self):
        result = []
        for path, tree in self.trees.items():
            if "/routers/" not in path and path != "src/web/main.py":
                continue
            prefix = ""
            for node in tree.body:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    if ast.unparse(node.value.func).endswith("APIRouter"):
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                prefix = kw.value.value
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for d in node.decorator_list:
                    if not isinstance(d, ast.Call) or not isinstance(d.func, ast.Attribute):
                        continue
                    if d.func.attr in HTTP and d.args and isinstance(d.args[0], ast.Constant):
                        result.append((prefix + d.args[0].value, d.func.attr, path, node))
        return result

def schema_type(schema):
    if not schema:
        return "без отдельной схемы"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    for option in ("anyOf", "oneOf", "allOf"):
        if option in schema:
            return " / ".join(schema_type(s) for s in schema[option])
    kind = schema.get("type", "объект")
    if kind == "array":
        kind = "список " + schema_type(schema.get("items", {}))
    if "format" in schema:
        kind += f" ({schema['format']})"
    return kind

def constraints(schema, field):
    parts = []
    if "default" in schema:
        value = schema["default"]
        value = "скрыто" if SENSITIVE.search(field) else json.dumps(value, ensure_ascii=False)
        parts.append("по умолчанию " + inline(value))
    if "enum" in schema:
        parts.append("значения " + ", ".join(map(inline, schema["enum"])))
    labels = {"minimum":"минимум", "exclusiveMinimum":"строго больше", "maximum":"максимум",
              "exclusiveMaximum":"строго меньше", "minLength":"мин. длина", "maxLength":"макс. длина",
              "minItems":"мин. элементов", "maxItems":"макс. элементов", "pattern":"шаблон"}
    for key, label in labels.items():
        if key in schema:
            parts.append(f"{label} {inline(schema[key])}")
    return ", ".join(parts) or "—"

def body_schema(spec, root):
    return ", ".join(f"{schema_type(detail.get('schema', {}))} ({mime})"
                     for mime, detail in spec.get("content", {}).items()) or "—"

def route_subject(path):
    if path.startswith("/auth/"):
        return ("Контур сотрудника" if "/admin/" in path else "Контур пользователя клиента") + (
            ", учётные данные" if path.endswith("/login") else ", токены текущей сессии"
        )
    if path.startswith("/admin/"):
        return "Внутренний сотрудник (Admin), проверка действующей учётной записи"
    if path.startswith("/user/"):
        return "Пользователь клиента (User), проверка действующей учётной записи"
    return "Общедоступный маршрут"

def api_catalog(source, api, summaries):
    # OpenAPI summaries are the project's English operation labels. Verbs from the
    # path and the applied method clarify the operation in the Russian narrative.
    definitions = source.routes()
    lookup = {(route, verb): (file, node) for route, verb, file, node in definitions}
    lines = ["## Приложение A. Полный справочник HTTP-маршрутов", "",
             "Контракт извлечён из реально запущенного OpenAPI на синтетической БД и сопоставлен со статическими обработчиками. Указанные коды OpenAPI описывают объявленный ответ. Дополнительные коды из общего обработчика и ветвей доступа применяются при соответствующем условии. Столбцы прав показывают коды, читаемые в ветвях, а не логическое «И». Условия вместе с примерами приведены в основных разделах.",
             "", "OpenAPI доступен через `/openapi.json`, Swagger UI через `/docs` и ReDoc через `/redoc`. Эти служебные маршруты добавляет FastAPI и не включает в каталог ниже.", ""]
    results = []
    tag = None
    for path, operations in sorted(api["paths"].items()):
        for verb, item in sorted(operations.items()):
            if verb not in HTTP:
                continue
            group = "/".join(path.split("/")[:3]) if path != "/health" else "/health"
            if group != tag:
                lines.extend([f"### Группа {group}", ""])
                tag = group
            bound = lookup.get((path, verb))
            if not bound:
                prefix = item.get("operationId", "")
                matches = [(f, n) for _p, h, f, n in definitions if h == verb
                           and prefix.startswith(n.name + "_")]
                if len(matches) == 1:
                    bound = matches[0]
            identifier = re.sub(r"[^a-zA-Z0-9]+", "-", f"{verb}-{path}").strip("-").lower()
            summary = item.get("summary", "Операция")
            lines.extend([f"#### {verb.upper()} {path} {{#api-{identifier}}}", "",
                          f"{summaries.get(summary, summary)}. {route_subject(path)}.", ""])
            prefix = next((prefix for prefix in SERVICE_FILES if path.startswith(prefix)), "")
            service = SERVICE_FILES.get(prefix, "")
            targets, rights, used, errors = [], [], [], []
            if bound:
                file, node = bound
                lines.extend([f"**Обработчик** — {source.link(file, node, node.name)}.", ""])
                if service:
                    target_file = f"src/application/services/{service}.py"
                    role_realm = path.split("/")[3] if service == "role_service" else None
                    targets, rights, used, errors = source.trace(file, node, target_file, role_realm)
            if prefix:
                lines.extend([SERVICE_POLICY[service], ""])
            if targets:
                lines.extend(["**Прикладные вызовы** — " + " · ".join(targets) + ".", ""])
            if rights:
                lines.extend(["**Метки разрешений из ветвей** — " + ", ".join(map(inline, rights)) + ".", ""])
            elif prefix and "/permissions" not in path:
                lines.extend(["**Разрешения** — см. прикладной вызов и матрицу доступа. "
                              "В отобранных ветвях отсутствует прямая ссылка на enum права.", ""])
            if used:
                lines.extend(["**Поля DTO, прочитанные прикладными методами** — " + ", ".join(map(inline, used)) + ".", ""])
            request = item.get("requestBody", {})
            lines.append(f"**Тело** — {body_schema(request, api)}"
                         + (" (обязательно)." if request.get("required") else " (необязательно или отсутствует)."))
            parameters = item.get("parameters", [])
            if parameters:
                lines.extend(["", "| Параметр | Где | Тип | Наличие и ограничения |", "|---|---|---|---|"])
                for parameter in parameters:
                    schema = parameter.get("schema", {})
                    need = "обязателен" if parameter.get("required") else "можно опустить"
                    lines.append(f"| {tbl(inline(parameter['name']))} | {parameter['in']} | {tbl(schema_type(schema))} | "
                                 f"{need}. {tbl(constraints(schema, parameter['name']))} |")
            else:
                lines.append("Параметры пути, строки запроса и явно описанные заголовки отсутствуют.")
            lines.extend(["", "**Ответ OpenAPI** — " + " · ".join(
                f"{status} {body_schema(response, api)}" for status, response in item.get("responses", {}).items()) + "."])
            if path.startswith(("/admin/", "/user/")):
                lines.append("Учётные данные или сессия могут дать 401, отсутствие разрешения — 403. "
                             "Прикладное ограничение области и состояния может дать доменный 400.")
            elif path.startswith("/auth/"):
                lines.append("Неверные учётные данные либо токен могут дать 401. Ошибка формы даёт 422 при её валидации.")
            if errors:
                lines.append("Прямые исключения маршрута или выбранных прикладных ветвей — "
                             + ", ".join(map(inline, errors)) + ". Сопоставление кодов см. в разделе обработки ошибок.")
            if any(p.get("name", "").lower() == "idempotency-key" for p in parameters):
                lines.append("Повтор с тем же ключом может вернуть сохранённый успех. Изменённый отпечаток даёт 409, "
                             "занятость БД может дать 503. См. BR-022.")
            lines.append("")
            results.append({"method": verb.upper(), "path":path, "anchor":f"api-{identifier}",
                            "file":bound[0] if bound else None, "line":bound[1].lineno if bound else None,
                            "handler":bound[1].name if bound else None, "rights":rights})
    lines.extend(["### Схемы входов и ответов OpenAPI", "",
                  "Обязательность поля следует из списка required. Тип null в объединении представляет допустимое явное пустое значение; "
                  "отсутствие поля обрабатывается по умолчанию, показанному в таблице. "
                  "Прикладные и доменные правила могут дополнительно отклонять допустимое по OpenAPI значение.", ""])
    for name, schema in sorted(api.get("components", {}).get("schemas", {}).items()):
        lines.extend([f"#### {name}", ""])
        if not schema.get("properties"):
            lines.extend([f"Форма — {schema_type(schema)}. {constraints(schema, name)}.", ""])
            continue
        extra = schema.get("additionalProperties")
        if extra is False:
            lines.extend(["Дополнительные поля запрещены схемой.", ""])
        lines.extend(["| Поле | Тип | Обязательность | Значение и ограничения |", "|---|---|---|---|"])
        required = set(schema.get("required", []))
        for field, details in schema["properties"].items():
            lines.append(f"| {tbl(inline(field))} | {tbl(schema_type(details))} | "
                         f"{'обязательно' if field in required else 'можно опустить'} | {tbl(constraints(details, field))} |")
        lines.append("")
    return "\n".join(lines), results

def sql_catalog(source, tables):
    meanings = {
        "accounts":"Учётные данные и отдельное состояние доступа.",
        "admins":"Расширение записи сотрудника для внутреннего контура.",
        "admins_roles":"Назначения административных ролей сотрудникам.",
        "auth_refresh_sessions":"Хеши refresh, идентификация субъекта и абсолютное время окончания.",
        "clients":"Организации-заказчики и ответственный внутренний сотрудник.",
        "creation_results":"Резервирование ключа и сохранённый успешный результат создания.",
        "departments":"Отделы исполнителей и маршрутизации заявок.",
        "employees":"Общие данные внутреннего сотрудника или пользователя клиента.",
        "roles":"Названия, область и список кодов разрешений роли.",
        "ticket_comments":"Хронология самостоятельных комментариев внутренней заявки.",
        "ticket_status_records":"История внутренних переходов и эпизодов работы.",
        "tickets":"Внутренняя служебная сторона заявки и текущие поля.",
        "user_tickets":"Пользовательская карточка обращения.",
        "user_tickets_comment":"Самостоятельные комментарии внешней карточки.",
        "user_tickets_status_record":"Пользовательские переходы и авторы.",
        "users":"Расширение сотрудника-пользователя связью с клиентом.",
        "users_roles":"Назначения ролей в пользовательском контуре.",
    }
    ddl_lines = (source.root / "db" / "schema.sql").read_text().splitlines()
    result = ["## Приложение B. Таблицы SQLite", "",
              "Сведения получены из временной базы с `db/schema.sql` через PRAGMA. "
              "В SQLite `INTEGER PRIMARY KEY` может служить rowid даже при пустом флаге notnull в PRAGMA. "
              "Внешние ключи таблицы и зависимости, проверяемые приложением, различаются. "
              "Связь, которой нет в списке FK, сама по себе не обеспечивается SQLite.", ""]
    for name, table in tables.items():
        ddl = next((i for i, line in enumerate(ddl_lines, 1)
                    if line.lower().startswith(f"create table {name.lower()} ")), None)
        result.extend([f"### Таблица {name} {{#db-{name.replace('_', '-')}}}", "",
                       f"{meanings.get(name, 'Таблица прикладного хранения.')} {source.link('db/schema.sql', label='DDL', line=ddl)}.", "",
                       "| Столбец | Тип | Ограничения и умолчание |", "|---|---|---|"])
        for field in table["columns"]:
            requirements = []
            if field["pk"]:
                requirements.append(f"PK {field['pk']}")
            if field["notnull"]:
                requirements.append("NOT NULL")
            if field["dflt_value"] is not None:
                requirements.append(f"DEFAULT {inline(field['dflt_value'])}")
            result.append(f"| {inline(field['name'])} | {inline(field['type'] or 'без типа')} | {tbl(', '.join(requirements) or '—')} |")
        result.append("")
        if table["foreign_keys"]:
            keys = [
                f"{inline(rel['from'])} → {inline(rel['table'] + '.' + rel['to'])}, удаление {inline(rel['on_delete'])}, обновление {inline(rel['on_update'])}"
                for rel in table["foreign_keys"]
            ]
            result.extend(["Внешние ключи — " + " · ".join(keys) + ".", ""])
        else:
            result.extend(["Внешние ключи отсутствуют.", ""])
        if table["indexes"]:
            indexes = [f"{inline(i['name'])} ({', '.join(('выражение' if c is None else inline(c)) for c in i['columns'])})"
                       + (" UNIQUE" if i["unique"] else "") for i in table["indexes"]]
            result.extend(["Индексы — " + " · ".join(indexes) + ".", ""])
        else:
            result.extend(["PRAGMA index_list не показывает отдельных индексов.", ""])
        if "CHECK" in table["ddl"].upper():
            result.extend(["Ограничения CHECK приведены в DDL по ссылке выше. Для служебных таблиц их смысл описан в разделе хранения.", ""])
    return "\n".join(result)

def function_signature(node):
    arguments = node.args
    params = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    defaults = {arg.arg: value for arg, value in
                zip([*arguments.posonlyargs, *arguments.args][-(len(arguments.defaults) or 10**6):], arguments.defaults)}
    defaults.update({arg.arg:value for arg, value in zip(arguments.kwonlyargs, arguments.kw_defaults) if value})
    arguments_text = []
    for argument in params:
        if argument.arg in {"self", "cls"}:
            continue
        text = argument.arg
        if argument.annotation:
            text += ": " + ast.unparse(argument.annotation)
        if argument.arg in defaults:
            value = defaults[argument.arg]
            if isinstance(value, ast.Constant) and (not SENSITIVE.search(argument.arg) or value.value is None):
                text += " = " + (repr(value.value) if not isinstance(value.value, str) or not value.value else "строка")
            else:
                text += " = вычисляемое значение"
        arguments_text.append(text)
    if arguments.vararg:
        arguments_text.append("*" + arguments.vararg.arg)
    if arguments.kwarg:
        arguments_text.append("**" + arguments.kwarg.arg)
    return ", ".join(map(inline, arguments_text)) or "без аргументов кроме экземпляра"

def class_fields(node):
    result = []
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            name = item.target.id
            suffix = ""
            if item.value is not None:
                if SENSITIVE.search(name):
                    suffix = " (значение не приводится)"
                elif isinstance(item.value, ast.Constant) and not isinstance(item.value.value, str):
                    suffix = " = " + repr(item.value.value)
                else:
                    suffix = " (с умолчанием)"
            result.append(inline(name + ": " + ast.unparse(item.annotation) + suffix))
    return result

def module_purpose(path):
    if path == "src/web/main.py":
        return "Сборка FastAPI, подключение роутеров, обработчиков исключений и служебной проверки."
    if path == "scripts/migrate_backend_storage.py":
        return "Ограниченный переход схемы к версиям сущностей, общим refresh-сессиям и результатам создания."
    if path in {"main.py","config.py","models.py"} or path.startswith("src/oauth2/"):
        return "Исторический модуль верхнего уровня. Использование в штатной сборке определяется по импортам."
    purpose = [
        ("/gateways/", "SQL именованных операций конкретного хранилища"),
        ("/mappers/", "Преобразование строк/параметров хранения и доменных объектов"),
        ("src/adapters/repositories/", "SQLite-реализация операций выборки, сохранения и контроля версий"),
        ("src/adapters/uow/", "Адаптация unit of work и объединение репозиториев на соединении"),
        ("src/application/services/", "Оркестрация прикладных операций с UoW, правами и агрегатами"),
        ("src/application/dto/", "Контракты передачи данных между входом, сервисами и ответом"),
        ("src/application/assemblers/", "Преобразование доменных объектов в выходные DTO"),
        ("src/application/helper/", "Общие прикладные проверки действующего субъекта"),
        ("src/domain/repositories/", "Абстрактный контракт хранилища, используемый доменом и приложением"),
        ("src/domain/services/", "Доменные правила, связывающие агрегаты или разные части операции"),
        ("src/domain/statuses/", "Предметная модель переходов, состояния или записи истории"),
        ("src/domain/policies/", "Доменная политика доступа либо проверки состояния субъекта"),
        ("src/domain/rbac/", "Контур ролей и разрешений: контракт, enum или обработка назначений"),
        ("src/domain/", "Предметная модель, контракт либо общий доменный модуль"),
        ("src/web/routers/", "Входные операции FastAPI, DTO и преобразование результата"),
        ("src/web/models/", "Валидация входов или форма HTTP-ответов"),
        ("src/web/dependencies/", "Зависимости FastAPI и формирование контекста запроса"),
        ("src/web/auth/", "Проверка субъекта, токены и операции сессии"),
        ("src/web/", "Общая часть HTTP-адаптера и его конфигурации"),
        ("utils/db/", "Технический слой выполнения запросов, ошибок и соединений"),
        ("utils/http/", "Утилиты HTTP-представления"),
    ]
    if path.endswith("/__init__.py"):
        return "Граница пакета. Реэкспорты и импортируемые определения указаны ниже."
    return next((description + "." for prefix, description in purpose if prefix in path),
                "Вспомогательный модуль, подключаемый указанными вызывающими сторонами.")

def module_catalog(source):
    reverse = defaultdict(list)
    for path, imports in {**source.imports, **source.tests}.items():
        for name in imports:
            reverse[name].append(path)
    lines = ["## Приложение C. Справочник исходного кода", "",
             "Для каждого Python-модуля указаны его назначение, символы, параметры и выходные аннотации. "
             "Обратные связи показывают статические импорты, включая тесты. Интерфейсные обращения через внедрение "
             "зависимостей раскрыты в описании операций. Список прямых исключений и вызовов записи извлечён из тела "
             "символа и не подменяет распространение ошибок из зависимостей. Прямой импорт из теста подтверждает связь "
             "с тестовым модулем. Для сквозного покрытия см. [сценарии валидации](meta/validation.md).", ""]
    coverage = []
    current_group = None
    for path in source.trees:
        group = "/".join(path.split("/")[:2]) if path.startswith(("src/", "utils/")) else "Корневые и сервисные модули"
        if group != current_group:
            group_label = inline(group) if group.startswith(("src/", "utils/")) else group
            lines.extend([f"### {group_label}", ""])
            current_group = group
        anchor = "module-" + re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-").lower()
        module = (path[:-3].replace("/", ".")).removesuffix(".__init__")
        imports = source.imports[path]
        callers = [p for p in reverse.get(module, []) if p != path]
        direct = [p for p in callers if p.startswith("tests/")]
        coverage.append({"path":path, "anchor":anchor, "symbols":len(source.nodes[path]), "tests":direct})
        lines.extend([f"#### {inline(path)} {{#{anchor}}}", "", module_purpose(path), "",
                      "**Импорты** — " + (", ".join(map(inline, imports)) if imports else "без импортов") + ".",
                      "**Прямые импортеры** — " + (", ".join(map(inline, callers)) if callers else "нет установленных") + ".",
                      "**Тесты с прямым импортом** — " + (", ".join(map(inline, direct)) if direct else "отдельный прямой импорт не найден") + ".",
                      "", source.link(path, label="Исходник модуля") + ".", ""])
        nodes = source.nodes[path]
        for qualified, node in nodes:
            if isinstance(node, ast.ClassDef):
                bases = ", ".join(map(lambda expression: inline(ast.unparse(expression)), node.bases))
                fields = class_fields(node)
                detail = " · основы " + bases if bases else ""
                if fields:
                    detail += " · поля " + ", ".join(fields)
                lines.append(f"- **{qualified}**{detail}. {source.link(path, node, 'Определение')}.")
                continue
            returned = inline(ast.unparse(node.returns)) if node.returns else (
                "значение по реализации" if any(isinstance(x, ast.Return) and x.value is not None
                                                  for x in ast.walk(node)) else "без отдельного значения"
            )
            raised = source.action_errors(node)
            effects = sorted(Source.attributes(node) & {
                "save", "delete", "commit", "rollback", "touch", "rotate", "revoke_subject",
                "revoke_account", "append_status", "add_comment", "mkdir", "execute", "write_text",
                "execute_many", "executescript", "connect", "close", "create_query", "disable",
                "enable", "sync_from_ticket", "sync_from_ticket_user",
            })
            detail = ""
            if effects:
                detail += " Связанные вызовы " + ", ".join(map(inline, effects)) + "."
            if raised:
                detail += " Прямые исключения " + ", ".join(map(inline, raised)) + "."
            lines.append(f"- **{qualified}**. Вход {function_signature(node)}. Выход {returned}.{detail} "
                         + source.link(path, node, "Символ") + ".")
        if not nodes:
            lines.append("Объявления классов или функций верхнего уровня отсутствуют. Константы, импорты и таблицы см. по ссылке на модуль.")
        lines.append("")
    return "\n".join(lines), coverage

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("revision")
    parser.add_argument("runtime", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--summaries", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = Source(args.source, args.revision)
    api, routes = api_catalog(source, read_json(args.runtime / "openapi.json"),
                              read_json(args.summaries) if args.summaries else {})
    sql = sql_catalog(source, read_json(args.runtime / "tables.json"))
    modules, module_index = module_catalog(source)
    write(args.output / "api.md", api)
    write(args.output / "schema.md", sql)
    write(args.output / "modules.md", modules)
    index = {"routes": routes, "modules": module_index,
             "tables": sorted(read_json(args.runtime / "tables.json"))}
    write(args.output / "catalog-index.json", json.dumps(index, ensure_ascii=False, indent=2))
    unresolved = [r["path"] for r in routes if r["file"] is None]
    print(f"{len(routes)} операций, {len(module_index)} модулей, {len(index['tables'])} таблиц; "
          f"без статического шаблона: {unresolved}")

if __name__ == "__main__":
    main()
