const queues = ["open", "all", "closed", "hotline"];
const sorts = ["created-desc", "created-asc", "id-desc", "id-asc"];
const sizes = [25, 50];
export const directoryPaths = Object.freeze({
  clients: "/clients",
  users: "/users",
  admins: "/admins",
  departments: "/departments",
  adminRoles: "/roles/admin",
  userRoles: "/roles/user",
});

export const queueOptions = Object.freeze(queues);
export const sizeOptions = Object.freeze(sizes);

function positiveInteger(value) {
  if (!value || !/^\d+$/.test(value)) return null;
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : null;
}

export function readRoute(pathname, search = "") {
  if (pathname === "/login") return { page: "login" };
  const directory = readDirectory(pathname);
  if (directory) return directory;
  if (pathname === "/tickets/new" || pathname === "/tickets/new/") return { page: "newTicket" };
  if (pathname === "/" || pathname === "/tickets" || pathname === "/tickets/") {
    const params = new URLSearchParams(search);
    const queue = params.get("queue");
    const sort = params.get("sort");
    const size = positiveInteger(params.get("size"));
    return {
      page: "queue",
      queue: queues.includes(queue) ? queue : "open",
      sort: sorts.includes(sort) ? sort : "created-desc",
      number: positiveInteger(params.get("page")) ?? 1,
      size: sizes.includes(size) ? size : 25,
    };
  }
  const detail = /^\/tickets\/(\d+)\/?$/.exec(pathname);
  const id = positiveInteger(detail?.[1]);
  if (id) return { page: "ticket", id };
  const relation = /^\/tickets\/(\d+)\/(client|user)\/(\d+)\/?$/.exec(pathname);
  const ticketId = positiveInteger(relation?.[1]);
  const relatedId = positiveInteger(relation?.[3]);
  return ticketId && relatedId
    ? { page: "related", id: ticketId, type: relation[2], relatedId }
    : { page: "notFound" };
}

function readDirectory(pathname) {
  const path = pathname.replace(/\/$/, "");
  if (path === "/roles") return { page: "roleIndex" };
  for (const [resource, base] of Object.entries(directoryPaths)) {
    if (path === base) return { page: "directory", resource, mode: "list" };
    if (!path.startsWith(`${base}/`)) continue;
    const suffix = path.slice(base.length + 1);
    if (suffix === "new") return { page: "directory", resource, mode: "create" };
    const detail = /^(\d+)(\/edit)?$/.exec(suffix);
    const id = positiveInteger(detail?.[1]);
    if (id) return { page: "directory", resource, mode: detail[2] ? "edit" : "detail", id };
  }
  return null;
}

export function directoryPath(resource, mode, id) {
  const base = directoryPaths[resource];
  if (mode === "create") return `${base}/new`;
  if (!id) return base;
  return `${base}/${id}${mode === "edit" ? "/edit" : ""}`;
}

export const ticketPath = (id) => `/tickets/${id}`;
export const relatedPath = (id, type, relatedId) => `${ticketPath(id)}/${type}/${relatedId}`;

export function queuePath({ queue = "open", sort = "created-desc", number = 1, size = 25 } = {}) {
  const params = new URLSearchParams({ queue, sort, page: String(number) });
  if (size !== 25) params.set("size", String(size));
  return `/tickets?${params}`;
}
