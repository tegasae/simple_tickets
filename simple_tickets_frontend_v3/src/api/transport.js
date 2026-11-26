import { createAuth, isTokenString } from './auth.js';

const API_PREFIX = '/api';
const PATH_ORIGIN = 'https://simple-tickets.invalid';
const REQUEST_TIMEOUT_MS = 15_000;

const HTTP_CODES = new Map([
  [400, 'invalid-operation'],
  [401, 'unauthorized'],
  [403, 'forbidden'],
  [404, 'not-found'],
  [409, 'conflict'],
  [422, 'validation'],
  [503, 'unavailable'],
]);

export class ApiError extends Error {
  constructor(status, code = HTTP_CODES.get(status) ?? 'http', fields = []) {
    super(code);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = Object.freeze([...fields]);
  }
}

function assertAdminPath(path) {
  if (typeof path !== 'string' || !path.startsWith('/admin/') || /[\\#\s]/u.test(path)) {
    throw new ApiError(0, 'invalid-request');
  }
  const target = new URL(path, PATH_ORIGIN);
  if (target.origin !== PATH_ORIGIN || !target.pathname.startsWith('/admin/')) {
    throw new ApiError(0, 'invalid-request');
  }
  return target.pathname + target.search;
}

async function runUntilAborted(signal, operation) {
  signal.throwIfAborted();
  let abort;
  const interrupted = new Promise((_, reject) => {
    abort = () => reject(signal.reason);
    signal.addEventListener('abort', abort, { once: true });
  });
  try {
    const pending = Promise.resolve().then(() => {
      signal.throwIfAborted();
      return operation();
    });
    return await Promise.race([pending, interrupted]);
  } finally {
    signal.removeEventListener('abort', abort);
  }
}

function validationFields(payload) {
  if (!Array.isArray(payload?.detail)) return [];
  const fields = payload.detail.flatMap((problem) => {
    const location = problem?.loc;
    if (!Array.isArray(location) || location[0] !== 'body') return [];
    const field = location[1];
    return typeof field === 'string' && /^[a-z][a-z0-9_]{0,63}$/.test(field) ? [field] : [];
  });
  return [...new Set(fields)];
}

export function createApi({ fetchImpl = globalThis.fetch, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  async function request(path, { method = 'GET', body, json, accessToken, idempotencyKey, signal, validate, expectedStatus } = {}) {
    const headers = new Headers({ Accept: 'application/json' });
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }
    if (idempotencyKey !== undefined) {
      headers.set('Idempotency-Key', idempotencyKey);
    }
    if (json !== undefined) {
      headers.set('Content-Type', 'application/json');
      body = JSON.stringify(json);
    } else if (body instanceof URLSearchParams) {
      headers.set('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8');
    }

    const deadline = AbortSignal.timeout(timeoutMs);
    const requestSignal = signal ? AbortSignal.any([signal, deadline]) : deadline;
    let validationRejected = false;
    try {
      return await runUntilAborted(requestSignal, receive);
    } catch (error) {
      if (deadline.aborted && requestSignal.reason === deadline.reason) {
        throw validationRejected ? new ApiError(422) : new ApiError(0, 'timeout');
      }
      throw error;
    }

    async function receive() {
      let response;
      try {
        response = await fetchImpl(API_PREFIX + path, {
          method,
          headers,
          body,
          signal: requestSignal,
          redirect: 'error',
          credentials: 'omit',
          cache: 'no-store',
        });
      } catch (error) {
        if (requestSignal.aborted || error?.name === 'AbortError') {
          throw error;
        }
        throw new ApiError(0, 'network');
      }
      requestSignal.throwIfAborted();
      if (!response.ok) {
        if (response.status === 422) {
          validationRejected = true;
          let fields = [];
          try {
            fields = validationFields(await response.json());
          } catch {
            // The HTTP rejection stands even when its optional field data cannot be read.
          }
          requestSignal.throwIfAborted();
          throw new ApiError(422, 'validation', fields);
        }
        throw new ApiError(response.status);
      }

      if (expectedStatus !== undefined && response.status !== expectedStatus) {
        throw new ApiError(response.status, 'invalid-response');
      }
      let payload = null;
      if (response.status !== 204) {
        try {
          payload = await response.json();
        } catch (error) {
          if (requestSignal.aborted || error?.name === 'AbortError') {
            throw error;
          }
          throw new ApiError(response.status, 'invalid-response');
        }
      }
      requestSignal.throwIfAborted();
      if (validate && !validate(payload)) {
        throw new ApiError(response.status, 'invalid-response');
      }
      return payload;
    }
  }

  return {
    ...createAuth(request),
    async get(path, { accessToken, signal } = {}) {
      if (!isTokenString(accessToken)) {
        throw new ApiError(401);
      }
      return request(assertAdminPath(path), { accessToken, signal });
    },
    async mutate(path, { method, json, idempotencyKey, accessToken, signal, expectedStatus } = {}) {
      if (!isTokenString(accessToken)) {
        throw new ApiError(401);
      }
      const target = assertAdminPath(path);
      const isObject = json && typeof json === 'object' && !Array.isArray(json);
      const revoking = /^\/admin\/(admins|users)\/[1-9]\d*\/roles$/.test(target);
      const toggle = /^\/admin\/(clients|users|admins|departments)\/[1-9]\d*\/(?:account\/)?(?:enable|disable)$/.test(target);
      if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) ||
          (method === 'DELETE' ? (revoking ? !isObject : json !== undefined)
            : method === 'PATCH' && toggle ? json !== undefined : !isObject)) {
        throw new ApiError(0, 'invalid-request');
      }
      if (idempotencyKey !== undefined &&
          (method !== 'POST' || !isTokenString(idempotencyKey) || idempotencyKey.length > 128)) {
        throw new ApiError(0, 'invalid-request');
      }
      return request(target, { method, json, idempotencyKey, accessToken, signal, expectedStatus });
    },
  };
}
