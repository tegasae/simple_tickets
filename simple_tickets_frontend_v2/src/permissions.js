export const ADMIN_PERMISSIONS = Object.freeze({
  CLIENT_OPERATION: "client.operation",
  CLIENT_VIEW: "client.view",
  ADMIN_OPERATION: "admin.operation",
  ADMIN_VIEW: "admin.view",
  USER_OPERATION: "user.operation",
  USER_VIEW: "user.view",
  TICKET_OPERATION: "ticket.operation",
  TICKET_CREATED: "ticket.created",
  TICKET_VIEW: "ticket.view",
  TICKET_ACCEPTED: "ticket.accepted",
  TICKET_AT_WORK: "ticket.at_work",
  TICKET_AT_WORK_REMOTE: "ticket.at_work_remote",
  TICKET_AT_WORK_RETROSPECTIVE: "ticket.at_work_retrospective",
  TICKET_CANCELLED: "ticket.canceled",
  TICKET_EXECUTED: "ticket.executed",
  ROLE_ASSIGN: "role.assign",
  ROLE_USER_ASSIGN: "role_user.assign",
});

export function normalizePermissions(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload.map(String);
  if (Array.isArray(payload.permissions)) return payload.permissions.map(String);
  return [];
}

export function hasPermission(permissions, permission) {
  return Array.isArray(permissions) && permissions.includes(permission);
}

export function hasAnyPermission(permissions, required) {
  return required.some((permission) => hasPermission(permissions, permission));
}

export const can = {
  clientsView: (p) => hasPermission(p, ADMIN_PERMISSIONS.CLIENT_VIEW),
  clientsOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.CLIENT_OPERATION),
  usersView: (p) => hasPermission(p, ADMIN_PERMISSIONS.USER_VIEW),
  usersOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.USER_OPERATION),
  adminsView: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_VIEW),
  adminsOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_OPERATION),
  ticketsView: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_VIEW),
  ticketsOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_OPERATION),
  ticketsCreate: (p) => hasAnyPermission(p, [ADMIN_PERMISSIONS.TICKET_CREATED, ADMIN_PERMISSIONS.TICKET_OPERATION]),
  ticketsAccept: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_ACCEPTED),
  ticketsWork: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_AT_WORK),
  ticketsRemoteWork: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_AT_WORK_REMOTE),
  ticketsRetrospective: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_AT_WORK_RETROSPECTIVE),
  ticketsCancel: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_CANCELLED),
  ticketsExecute: (p) => hasPermission(p, ADMIN_PERMISSIONS.TICKET_EXECUTED),
  departmentsView: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_OPERATION),
  departmentsOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_OPERATION),
  rolesView: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_OPERATION),
  rolesOperate: (p) => hasPermission(p, ADMIN_PERMISSIONS.ADMIN_OPERATION),
  assignAdminRoles: (p) => hasPermission(p, ADMIN_PERMISSIONS.ROLE_ASSIGN),
  assignUserRoles: (p) => hasPermission(p, ADMIN_PERMISSIONS.ROLE_USER_ASSIGN),
};

export function canAccessPage(page, permissions) {
  switch (page) {
    case "tickets": return can.ticketsView(permissions);
    case "clients": return can.clientsView(permissions);
    case "users": return can.usersView(permissions);
    case "admins": return can.adminsView(permissions);
    case "departments": return can.departmentsView(permissions);
    case "roles": return can.rolesView(permissions);
    default: return false;
  }
}

export const PAGE_ORDER = ["tickets", "clients", "users", "admins", "departments", "roles"];

export const canClientOperate = can.clientsOperate;
export const canClientView = can.clientsView;
export const canUserOperate = can.usersOperate;
export const canUserView = can.usersView;
