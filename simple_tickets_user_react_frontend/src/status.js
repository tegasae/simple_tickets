export const STATUS = {
  created: { label: "Создана", tone: "info" },
  confirmed_by_admin: { label: "Принята", tone: "info" },
  in_work: { label: "В работе", tone: "ok" },
  waiting_for_confirmation: { label: "Ожидает подтверждения", tone: "warning" },
  execution_confirmed_by_user: { label: "Выполнение подтверждено вами", tone: "ok" },
  execution_confirmed_by_admin: { label: "Выполнение подтверждено", tone: "ok" },
  cancelled_by_user: { label: "Отменена вами", tone: "danger" },
  cancelled_by_admin: { label: "Отменена", tone: "danger" },
};

export const CLOSED_STATUSES = new Set([
  "execution_confirmed_by_user",
  "execution_confirmed_by_admin",
  "cancelled_by_user",
  "cancelled_by_admin",
]);

export function statusMeta(status) {
  return STATUS[status] || { label: status || "—", tone: "muted" };
}

export function canCancelByUser(ticket) {
  return ticket?.current_status === "created" && !ticket?.is_closed;
}

export function canConfirmByUser(ticket) {
  return ticket?.current_status === "waiting_for_confirmation" && !ticket?.is_closed;
}
