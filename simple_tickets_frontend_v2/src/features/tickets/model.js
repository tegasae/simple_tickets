import { locale, t } from "../../shared/i18n/messages.js";

let formatters;

function localFormatters() {
  if (formatters?.locale !== locale) {
    formatters = {
      locale,
      date: new Intl.DateTimeFormat(locale, {
        year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
      }),
      number: new Intl.NumberFormat(locale),
    };
  }
  return formatters;
}

export function normalizeStatus(value) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

export function statusLabel(value) {
  const status = normalizeStatus(value);
  return status ? t(`status.${status}`, {}, status) : t("common.missing");
}

export function urgencyLabel(urgency) {
  return urgency ? t(`urgency.${urgency}`, {}, urgency) : t("common.missing");
}

export function timestamp(value) {
  if (typeof value !== "string" || !value) return null;
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : null;
}

export function formatDateTime(value) {
  const time = timestamp(value);
  return time === null ? t("common.missing") : localFormatters().date.format(time);
}

export function formatNumber(value) {
  return localFormatters().number.format(value);
}

export function normalizeTicket(ticket) {
  const statuses = Array.isArray(ticket.statuses) ? ticket.statuses : [];
  return {
    ...ticket,
    statuses,
    comments: Array.isArray(ticket.comments) ? ticket.comments : [],
    status: normalizeStatus(statuses.at(-1)?.status),
    createdAt: statuses[0]?.date_created ?? null,
  };
}

const normalizedSearch = (value) => String(value ?? "").toLocaleLowerCase(locale).replaceAll("ё", "е");

export function selectTickets(rows, { search = "", status = "", urgency = "", sort = "created-desc" } = {}) {
  const query = normalizedSearch(search.trim()).replace(/^№\s*(?=\d)/, "");
  const ascending = sort.endsWith("-asc");
  const direction = ascending ? 1 : -1;
  const result = rows.filter((row) => {
    if (status && row.status !== status) return false;
    if (urgency && row.urgency !== urgency) return false;
    if (!query) return true;
    return [row.ticket_id, row.text_of_ticket, row.description, row.status, statusLabel(row.status)]
      .some((value) => normalizedSearch(value).includes(query));
  });

  return result.sort((a, b) => {
    if (sort.startsWith("id-")) return direction * (a.ticket_id - b.ticket_id);
    const first = timestamp(a.createdAt);
    const second = timestamp(b.createdAt);
    if (first === null && second !== null) return 1;
    if (second === null && first !== null) return -1;
    return first !== second ? direction * (first - second) : b.ticket_id - a.ticket_id;
  });
}

export function paginate(rows, page, size) {
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const current = Math.min(Math.max(1, page), pages);
  const start = (current - 1) * size;
  return { current, pages, start, rows: rows.slice(start, start + size) };
}
