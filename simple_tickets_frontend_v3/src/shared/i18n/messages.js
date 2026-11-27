import { fieldMessages } from "../../features/tickets/fieldMessages.js";
import { workflowMessages } from "../../features/tickets/workflow/workflowMessages.js";
import { directoryMessages } from "../../features/admin/directoryMessages.js";
import { appearanceMessages } from "../../features/appearance/appearanceMessages.js";

export const DEFAULT_LOCALE = "ru-RU";
export let locale = DEFAULT_LOCALE;

export const referenceMessages = Object.freeze({
  ...fieldMessages,
  ...workflowMessages,
  ...directoryMessages,
  ...appearanceMessages,
  "app.name": "Simple Tickets",
  "app.mark": "ST",
  "app.workspace": "Рабочее место сотрудника",
  "app.skip": "К содержимому",
  "app.navigation": "Основная навигация",
  "common.cancel": "Отмена",
  "directory.recheckingPermissions": "Проверяем актуальные права…",
  "directory.permissionsUnavailable": "Не удалось подтвердить права доступа",
  "directory.actionsTitle": "Действия с записью",
  "directory.action.enable": "Включить запись",
  "directory.action.disable": "Отключить запись",
  "directory.action.enable.help": "Запись «{name}» снова станет активной.",
  "directory.action.disable.help": "Запись «{name}» станет неактивной. Отключение может повлиять на связанные записи и доступ к системе.",
  "directory.action.attachAccount": "Подключить аккаунт",
  "directory.action.detachAccount": "Отвязать аккаунт",
  "directory.action.detachAccount.help": "Аккаунт «{name}» будет отвязан. Для входа потребуется новый аккаунт.",
  "directory.action.enableAccount": "Включить доступ",
  "directory.action.enableAccount.help": "Вход в аккаунт «{name}» будет разрешён.",
  "directory.action.disableAccount": "Отключить доступ",
  "directory.action.disableAccount.help": "Вход в аккаунт «{name}» будет отключён.",
  "directory.action.changePassword": "Сменить пароль",
  "directory.action.changeDepartment": "Изменить отдел",
  "directory.action.removeDepartment": "Снять назначение отдела",
  "directory.action.removeDepartment.help": "Сотрудник «{name}» будет исключён из своего отдела.",
  "directory.action.grantRoles": "Выдать роли",
  "directory.action.revokeRoles": "Отозвать роли",
  "directory.action.remove": "Удалить запись",
  "directory.action.remove.help": "Запись «{name}» № {id} будет удалена без возможности восстановления.",
  "directory.action.removeSelf.help": "Ваш профиль «{name}» № {id} будет удалён без возможности восстановления. Текущая сессия завершится.",
  "directory.actionConfirm": "Подтвердить",
  "directory.actionConfirmDelete": "Удалить без восстановления",
  "directory.actionBack": "К действиям",
  "directory.actionCheck": "Проверить состояние",
  "directory.actionCatalogEmpty": "Нет доступных вариантов.",
  "directory.actionCatalogError": "Не удалось загрузить список вариантов.",
  "directory.rolesSelection": "Выберите роли",
  "directory.departmentChoice": "Отдел",
  "directory.chooseDepartment": "Выберите отдел",
  "directory.accountLogin": "Логин",
  "directory.accountPassword": "Новый пароль",
  "directory.accountPasswordHint": "От 8 до 128 символов. Нужны заглавная и строчная латинские буквы, цифра и специальный символ. Пробелы запрещены.",
  "directory.accountOwnPassword": "После смены своего пароля потребуется войти снова.",
  "directory.accountStartEnabled": "Сразу разрешить вход",
  "directory.passwordUnconfirmed": "Ответ о смене пароля потерян. Карточка не позволяет проверить результат.",
  "directory.passwordStopCheck": "Завершить ожидание смены пароля",
  "directory.passwordCheckStopped": "Ожидание завершено. Результат смены пароля остаётся неизвестным.",
  "directory.writeSuccess": "Действие выполнено.",
  "directory.writeValidation": "Проверьте введённые данные.",
  "directory.deleteBlocked": "Сервер отклонил удаление. Проверьте связанные записи и состояние объекта.",
  "directory.writeStillUnconfirmed": "Проверка пока не подтвердила результат. Повторная запись заблокирована.",
  "directory.createReplayExpired": "Срок безопасного повтора истёк. Сначала проверьте справочник.",
  "directory.writeObserved": "Актуальная запись содержит внесённые изменения.",
  "directory.rolesPartial": "Состояние ролей № {applied} совпадает с запросом. Результат для ролей № {remaining} ещё не подтверждён.",
  "directory.rolesPending": "Карточка пока не подтверждает изменение ролей № {remaining}.",
  "directory.recordMissing": "Запись отсутствует в справочнике.",
  "common.missing": "—",
  "common.retry": "Повторить",
  "common.refresh": "Обновить",
  "common.reset": "Сбросить",
  "common.loading": "Загрузка…",
  "common.identifier": "№ {id}",
  "login.title": "Вход сотрудника",
  "login.username": "Логин",
  "login.password": "Пароль",
  "login.submit": "Войти",
  "login.pending": "Выполняем вход…",
  "login.invalid": "Не удалось войти. Проверьте логин и пароль.",
  "login.inputError": "Проверьте введённые данные.",
  "login.showPassword": "Показать пароль",
  "login.hidePassword": "Скрыть пароль",
  "session.restoring": "Восстанавливаем вход…",
  "session.expired": "Сессия завершилась. Войдите снова.",
  "session.logout": "Выйти",
  "session.logoutUnconfirmed": "Вы вышли из приложения. Сервер не подтвердил завершение сессии.",
  "session.storageUnavailable": "Браузер ограничил хранение сессии. После обновления страницы может потребоваться повторный вход.",
  "error.title": "Не удалось загрузить данные",
  "error.network": "Не удалось связаться с сервером. Проверьте подключение и повторите попытку.",
  "error.timeout": "Сервер долго не отвечает. Повторите попытку.",
  "error.busy": "Сервис временно недоступен. Повторите попытку позже.",
  "error.generic": "Произошла ошибка. Повторите попытку.",
  "error.forbidden": "Нет доступа",
  "error.noTicketsPermission": "У вашей учётной записи нет права просматривать заявки.",
  "error.notFound": "Страница не найдена",
  "error.ticketMissing": "Заявка не найдена. Вернитесь к списку заявок.",
  "queue.title": "Заявки",
  "queue.areas": "Выбор очереди",
  "queue.all": "Все",
  "queue.open": "Открытые",
  "queue.closed": "Закрытые",
  "queue.hotline": "Горячая линия",
  "queue.hotlineForbidden": "Нет доступа к очереди горячей линии.",
  "queue.search": "Поиск заявок",
  "queue.placeholder": "Номер, тема, статус",
  "queue.find": "Найти",
  "queue.filters": "Фильтры",
  "queue.filtersCount": "Фильтры ({count})",
  "queue.activeSearch": "Поиск: {value}",
  "queue.activeStatus": "Статус: {value}",
  "queue.activeUrgency": "Приоритет: {value}",
  "queue.clearStatus": "Убрать фильтр статуса",
  "queue.clearUrgency": "Убрать фильтр приоритета",
  "queue.any": "Все значения",
  "queue.pagination": "Страницы заявок",
  "queue.previous": "Назад",
  "queue.next": "Далее",
  "queue.pageSize": "Строк на странице",
  "queue.range": "{start}–{end} из {total}",
  "queue.tableScroll": "Прокрутите таблицу по горизонтали, чтобы увидеть все столбцы.",
  "queue.empty.title": "В этой очереди пока нет заявок",
  "queue.empty.search": "Подходящих заявок не найдено",
  "queue.empty.hint": "Измените запрос или сбросьте условия поиска.",
  "ticket.number": "№",
  "ticket.title": "Тема",
  "ticket.status": "Статус",
  "ticket.createdAt": "Дата создания",
  "ticket.client": "Клиент",
  "ticket.contact": "Контакт",
  "ticket.requester": "Заявитель",
  "ticket.executor": "Исполнитель",
  "ticket.department": "Отдел",
  "ticket.urgency": "Приоритет",
  "ticket.planned": "Запланировано",
  "ticket.description": "Описание",
  "ticket.references": "Связанные лица и реквизиты",
  "ticket.back": "К списку заявок",
  "ticket.comments": "Комментарии",
  "ticket.history": "История",
  "ticket.noComments": "Комментариев пока нет",
  "ticket.noHistory": "История пока пуста",
  "ticket.author": "Сотрудник № {id}",
  "ticket.remoteRecommended": "Рекомендовано для горячей линии",
  "work.newTicket": "Новая заявка",
  "work.openTickets": "Открытые заявки",
  "work.tabLabel": "№ {id} {title}",
  "work.dirty": "Есть несохранённые изменения",
  "work.closeTab": "Закрыть заявку № {id}",
  "work.closeTabOnly": "Закрыть вкладку",
  "work.closeTitle": "Несохранённые изменения в заявке № {id}",
  "work.closeDescription": "Сохраните изменения или решите, что сделать с черновиком.",
  "work.continue": "Продолжить редактирование",
  "work.discard": "Отбросить черновик",
  "work.saveClose": "Сохранить и закрыть",
  "work.edit": "Редактировать заявку",
  "work.save": "Сохранить изменения",
  "work.created": "Заявка № {id} создана.",
  "work.another": "Создать ещё одну",
  "work.openCreated": "Открыть заявку № {id}",
  "work.confirmed": "Изменения сохранены.",
  "work.partial": "Сохранена только часть правок. Остальные остались в черновике.",
  "work.unconfirmed": "Сервер не подтвердил результат. Перечитайте карточку перед новой попыткой.",
  "work.repeatIntent": "Повторить отправку",
  "work.unknownPost": "Ответ от сервера не получен. Повтор использует тот же ключ операции.",
  "work.replayExpired": "Истёк срок безопасного повтора. Сверьте данные перед созданием новой записи.",
  "work.commentSent": "Комментарий добавлен.",
  "work.validation": "Проверьте значение поля.",
  "work.writeRejected": "Сервер отклонил запись. Проверьте данные и состояние заявки.",
  "work.writeUnavailable": "Результат операции не подтверждён. Черновик сохранён.",
  "work.writeForbidden": "Нет права на выполнение операции.",
  "workflow.succeeded": "Действие выполнено.",
  "workflow.startedHotline": "Взято в работу на горячей линии",
  "workflow.conflict": "Состояние заявки изменилось. Проверьте актуальную карточку перед новым действием.",
  "workflow.reloaded": "Карточка обновлена. Проверьте текущее состояние.",
  "workflow.observed": "В истории найден переход с указанными параметрами.",
  "workflow.stillUnconfirmed": "Состояние заявки пока прежнее. Результат действия остаётся неизвестным.",
  "workflow.differentState": "В истории есть другое изменение. Результат отправленного действия остаётся неизвестным.",
  "workflow.closeTitle": "Действие по заявке № {id} не подтверждено",
  "workflow.closeDescription": "При закрытии вкладки данные для проверки результата и черновики будут удалены. Отправленное действие ещё может завершиться на сервере.",
  "workflow.closeDeleteDescription": "Черновик этой вкладки будет удалён. Результат удаления заявки можно будет проверить после повторного открытия.",
  "workflow.preReadFailed": "Не удалось проверить актуальное состояние заявки. Действие не отправлено.",
  "workflow.hotlineRejected": "Не удалось начать работу на горячей линии. Проверьте статус, рекомендацию и исполнителя. Для принятой заявки ваш отдел должен совпадать с отделом заявки.",
  "work.writeExpired": "Проверьте действующую сессию и повторите отправку вручную.",
  "work.conflicts": "На сервере изменились поля, которые вы редактируете.",
  "work.serverValue": "На сервере: {value}",
  "work.draftValue": "В черновике: {value}",
  "work.adoptBaseline": "Сверить с серверной версией",
  "work.schedule": "Плановая дата",
  "work.yes": "Да",
  "work.no": "Нет",
  "work.check": "Проверить результат",
  "work.fieldsApplied": "Сохранено: {fields}",
  "work.fieldsRemaining": "В черновике: {fields}",
  "relation.back": "К заявке № {id}",
  "relation.client": "Клиент № {id}",
  "relation.requester": "Заявитель № {id}",
  "relation.contact": "Контакт № {id}",
  "relation.noPermission": "Нет права на просмотр связанной карточки.",
  "relation.notFound": "Связанная карточка недоступна или больше не относится к заявке.",
  "relation.email": "Почта",
  "relation.phone": "Телефон",
  "relation.address": "Адрес",
  "relation.active": "Действующий",
  "relation.inactive": "Отключён",
  "status.created": "Создана",
  "status.created_from_request_user": "Создана по запросу клиента",
  "status.created_from_ticket_user": "Создана из заявки клиента",
  "status.rejected": "Отклонено",
  "status.accepted": "Принято",
  "status.deferred": "Отложено",
  "status.suspended": "Приостановлено",
  "status.assigned": "Назначено",
  "status.at_work": "В работе",
  "status.paused": "Работа приостановлена",
  "status.ready_for_review": "Ожидает проверки",
  "status.confirmed_by_user": "Подтверждено пользователем",
  "status.executed": "Выполнено",
  "status.cancelled": "Отменено",
  "status.cancelled_by_user": "Отменено пользователем",
  "urgency.normal": "Обычный",
  "urgency.urgent": "Срочный",
  "urgency.maintenance": "Обслуживание",
});

const PLACEHOLDER = /\{([A-Za-z_][A-Za-z0-9_]*)\}/g;
const listeners = new Set();
let overrides = Object.freeze(Object.create(null));
let revision = 0;

function isRecord(value) {
  if (value === null || typeof value !== "object") return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function hasExactFields(value, fields) {
  return isRecord(value) && Object.keys(value).length === fields.length &&
    fields.every((field) => Object.hasOwn(value, field));
}

function isLocaleId(value) {
  if (typeof value !== "string" || value.length > 63 || !/^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$/.test(value)) return false;
  try {
    return Intl.getCanonicalLocales(value)[0] === value;
  } catch {
    return false;
  }
}

export function validateLanguageCatalog(raw) {
  if (!hasExactFields(raw, ["version", "defaultLanguage", "languages"]) || raw.version !== 1 ||
      !isLocaleId(raw.defaultLanguage) || !Array.isArray(raw.languages)) return null;

  const seen = new Set();
  const languages = [];
  for (const language of raw.languages) {
    if (!hasExactFields(language, ["id", "label"]) || !isLocaleId(language.id) || seen.has(language.id) ||
        typeof language.label !== "string" || !language.label.trim() || language.label.length > 100 ||
        /\p{Cc}/u.test(language.label)) return null;
    seen.add(language.id);
    languages.push(Object.freeze({ id: language.id, label: language.label.trim() }));
  }
  if (!seen.has(raw.defaultLanguage)) return null;
  return Object.freeze({ defaultLanguage: raw.defaultLanguage, languages: Object.freeze(languages) });
}

function placeholderNames(text) {
  const names = new Set();
  const literal = text.replace(PLACEHOLDER, (_, name) => {
    names.add(name);
    return "";
  });
  return /[{}]/.test(literal) ? null : names;
}

function hasMatchingPlaceholders(key, value) {
  const expected = placeholderNames(referenceMessages[key]);
  const actual = placeholderNames(value);
  return expected !== null && actual !== null && expected.size === actual.size &&
    [...expected].every((name) => actual.has(name));
}

function validMessages(raw, omitDefaults = false) {
  const clean = Object.create(null);
  if (isRecord(raw)) {
    for (const [key, value] of Object.entries(raw)) {
      if (Object.hasOwn(referenceMessages, key) && typeof value === "string" && value.trim() &&
          (!omitDefaults || value !== referenceMessages[key]) && hasMatchingPlaceholders(key, value)) {
        clean[key] = value;
      }
    }
  }
  return Object.freeze(clean);
}

export function validateDictionary(raw, expectedId) {
  if (!hasExactFields(raw, ["version", "language", "messages"]) || raw.version !== 1 ||
      !isLocaleId(expectedId) || raw.language !== expectedId || !isRecord(raw.messages)) return null;
  return validMessages(raw.messages);
}

export function getMessageRevision() {
  return revision;
}

export function subscribeMessages(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function applyMessages(language, dictionary) {
  const validLanguage = isLocaleId(language);
  const nextLocale = validLanguage ? language : DEFAULT_LOCALE;
  const next = validMessages(validLanguage ? dictionary : null, true);
  const keys = Object.keys(next);
  if (nextLocale === locale && keys.length === Object.keys(overrides).length &&
      keys.every((key) => next[key] === overrides[key])) return false;

  locale = nextLocale;
  overrides = next;
  revision += 1;
  for (const listener of listeners) listener();
  return true;
}

export function t(key, parameters = {}, fallback = key) {
  const message = overrides[key] ?? (Object.hasOwn(referenceMessages, key) ? referenceMessages[key] : fallback);
  return message.replace(PLACEHOLDER, (placeholder, name) =>
    parameters != null && Object.hasOwn(parameters, name) ? String(parameters[name]) : placeholder,
  );
}

export function renderMessage(value) {
  if (typeof value === "string") return value;
  return typeof value?.key === "string" ? t(value.key, value.params) : "";
}

export function errorKey(error) {
  if (error?.code === "timeout") return "error.timeout";
  if (error?.code === "network" || error?.status === 0) return "error.network";
  if (error?.status === 503) return "error.busy";
  return "error.generic";
}

export const errorText = (error) => t(errorKey(error));
