import { ApiError } from '../transport.js';

const CLIENTS = '/admin/clients';
const USERS = '/admin/users';
const DEPARTMENTS = '/admin/departments';

function isId(value) {
  return Number.isSafeInteger(value) && value > 0;
}

function requireId(value) {
  if (!isId(value)) throw new ApiError(0, 'invalid-request');
  return value;
}

function isReference(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) &&
    typeof value.enabled === 'boolean';
}

function isClient(value) {
  return isReference(value) &&
    isId(value.client_id) &&
    [value.name, value.email, value.phone, value.address, value.description].every(
      (field) => typeof field === 'string',
    );
}

function isUser(value) {
  return isReference(value) &&
    isId(value.employee_id) &&
    isId(value.client_id) &&
    [value.first_name, value.last_name, value.email, value.phone, value.login].every(
      (field) => typeof field === 'string',
    ) &&
    typeof value.enabled_login === 'boolean';
}

function isDepartment(value) {
  return isReference(value) && isId(value.department_id) && typeof value.name === 'string';
}

function requireResponse(value, check) {
  if (!check(value)) throw new ApiError(200, 'invalid-response');
  return value;
}

export function createReferencesApi(session) {
  async function list(path, check, signal) {
    const items = await session.get(path, { signal });
    return requireResponse(items, (value) => Array.isArray(value) && value.every(check));
  }

  return {
    async clients({ signal } = {}) {
      return list(`${CLIENTS}/`, isClient, signal);
    },

    async client(clientId, { signal } = {}) {
      const id = requireId(clientId);
      const value = await session.get(`${CLIENTS}/${id}`, { signal });
      return requireResponse(value, (item) => isClient(item) && item.client_id === id);
    },

    async users(clientId, { signal } = {}) {
      const id = requireId(clientId);
      return list(`${USERS}/client/${id}`, (user) => isUser(user) && user.client_id === id, signal);
    },

    async user(employeeId, { signal } = {}) {
      const id = requireId(employeeId);
      const value = await session.get(`${USERS}/${id}`, { signal });
      return requireResponse(value, (item) => isUser(item) && item.employee_id === id);
    },

    async departments({ signal } = {}) {
      return list(`${DEPARTMENTS}/`, isDepartment, signal);
    },
  };
}
