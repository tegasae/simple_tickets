import { t } from "../../shared/i18n/messages.js";
import { isUnknownWrite } from "./workspaceState.js";

export function writeError(error, { idempotent = false } = {}) {
  if (error?.code === "replay-expired") return t("work.replayExpired");
  if (isUnknownWrite(error)) return t(idempotent ? "work.unknownPost" : "work.writeUnavailable");
  if (error.status === 401) return t("work.writeExpired");
  if (error.status === 403) return t("work.writeForbidden");
  return t("work.writeRejected");
}

export function fieldErrors(error) {
  return Object.fromEntries((error?.fields ?? []).map((field) => [field, t("work.validation")]));
}
