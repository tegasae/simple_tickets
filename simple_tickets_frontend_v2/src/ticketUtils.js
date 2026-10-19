const ACTIVE_EXECUTOR_STATUSES = new Set(["ASSIGNED", "AT_WORK", "PAUSED", "READY_FOR_REVIEW"]);
const TERMINAL_STATUSES = new Set(["REJECTED", "EXECUTED", "CANCELLED", "CANCELLED_BY_USER", "CONFIRMED_BY_USER"]);

const STATUS_LABELS = {
  CREATED: "Создано",
  CREATED_FROM_TICKET_USER: "Создано пользователем",
  REJECTED: "Отклонено",
  ACCEPTED: "Принято",
  DEFERRED: "Отложено",
  SUSPENDED: "Приостановлено",
  ASSIGNED: "Назначено",
  AT_WORK: "В работе",
  PAUSED: "Работа приостановлена",
  READY_FOR_REVIEW: "Ожидает проверки",
  CONFIRMED_BY_USER: "Подтверждено пользователем",
  EXECUTED: "Выполнено",
  CANCELLED: "Отменено",
  CANCELLED_BY_USER: "Отменено пользователем",
};

export function normalizeStatus(value) {
  if (!value) return "";
  return String(value).trim().toUpperCase();
}

export function statusLabel(value) {
  const status = normalizeStatus(value);
  return STATUS_LABELS[status] || status || "—";
}

export function getCurrentStatus(ticket) {
  if (!ticket) return "";
  if (ticket.current_status) return normalizeStatus(ticket.current_status);
  const statuses = Array.isArray(ticket.statuses) ? ticket.statuses : [];
  return normalizeStatus(statuses.at(-1)?.status);
}

export function getCurrentExecutorId(ticket) {
  if (!ticket) return 0;
  if (Number(ticket.current_executor_id) >= 0 && ticket.current_executor_id !== undefined && ticket.current_executor_id !== null) {
    return Math.max(0, Number(ticket.current_executor_id) || 0);
  }
  const status = getCurrentStatus(ticket);
  if (!ACTIVE_EXECUTOR_STATUSES.has(status)) return 0;
  const statuses = Array.isArray(ticket.statuses) ? ticket.statuses : [];
  for (let i = statuses.length - 1; i >= 0; i -= 1) {
    const record = statuses[i];
    const recordStatus = normalizeStatus(record?.status);
    if (recordStatus === "ASSIGNED") return Number(record?.executor_id || 0);
    if (!ACTIVE_EXECUTOR_STATUSES.has(recordStatus)) return 0;
  }
  return 0;
}

export function getLastExecutorId(ticket) {
  if (!ticket) return 0;
  if (ticket.last_executor_id !== undefined && ticket.last_executor_id !== null) {
    return Math.max(0, Number(ticket.last_executor_id) || 0);
  }
  const statuses = Array.isArray(ticket.statuses) ? ticket.statuses : [];
  for (let i = statuses.length - 1; i >= 0; i -= 1) {
    if (normalizeStatus(statuses[i]?.status) === "ASSIGNED") return Number(statuses[i]?.executor_id || 0);
  }
  return 0;
}

export function isTerminalStatus(status) {
  return TERMINAL_STATUSES.has(normalizeStatus(status));
}

export function previewText(value, limit = 50) {
  const text = String(value || "").trim();
  return text.length > limit ? `${text.slice(0, limit)}…` : text;
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("ru-RU", {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).format(date);
}

export function formatDuration(secondsValue) {
  const total = Math.max(0, Math.floor(Number(secondsValue || 0)));
  if (!total) return "0 мин";
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const parts = [];
  if (days) parts.push(`${days} д`);
  if (hours) parts.push(`${hours} ч`);
  if (minutes || !parts.length) parts.push(`${minutes} мин`);
  return parts.join(" ");
}

export function toUtcIsoFromLocal(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new Error("Некорректная дата");
  return date.toISOString();
}

export function toLocalInputValue(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

export function personName(person, fallback = "—") {
  if (!person) return fallback;
  return `${person.first_name || ""} ${person.last_name || ""}`.trim() || fallback;
}
