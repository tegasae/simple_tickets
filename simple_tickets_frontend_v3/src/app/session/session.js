import { isTokenString } from '../../api/auth.js';
import { ApiError, createApi } from '../../api/transport.js';

export const REFRESH_STORAGE_KEY = 'simple-tickets.v3.refresh';

const PERMISSIONS_PATH = '/admin/admins/permissions';
const TICKET_VIEW = 'ticket.view';
const NO_PERMISSIONS = Object.freeze([]);

function browserStorage() {
  try {
    return globalThis.sessionStorage ?? null;
  } catch {
    return null;
  }
}

function createContext(refreshToken = null) {
  return {
    controller: new AbortController(),
    accessToken: null,
    refreshToken,
    bootstrap: null,
    login: null,
    refresh: null,
    permissions: null,
    permissionRevision: 0,
  };
}

function contextSignal(context, signal) {
  return signal ? AbortSignal.any([context.controller.signal, signal]) : context.controller.signal;
}

function actorIdFromToken(token) {
  try {
    const segments = token.split('.');
    if (segments.length !== 3) {
      return null;
    }
    const claims = JSON.parse(atob(segments[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (claims.subject_type === 'admin' && typeof claims.sub === 'string' && /^[1-9]\d*$/.test(claims.sub)) {
      const id = Number(claims.sub);
      return Number.isSafeInteger(id) ? id : null;
    }
  } catch {
    // Decoded claims are only used to choose a view. The server authorizes every request.
  }
  return null;
}

function safeError(error) {
  if (error instanceof ApiError) {
    return error;
  }
  if (Number.isInteger(error?.status) && error.status >= 400 && error.status <= 599) {
    return new ApiError(error.status);
  }
  return new ApiError(0, 'network');
}

export function createSession({ api = createApi(), storage = browserStorage() } = {}) {
  const subscribers = new Set();
  let storageAvailable = Boolean(storage);
  let current = createContext(readSavedRefresh());
  let snapshot = makeSnapshot(current.refreshToken ? 'restoring' : 'anonymous');

  function makeSnapshot(phase, updates = {}) {
    return Object.freeze({
      phase,
      permissions: NO_PERMISSIONS,
      actorId: null,
      error: null,
      logoutStatus: null,
      storageAvailable,
      ...updates,
    });
  }

  function publish(phase, updates) {
    snapshot = makeSnapshot(phase, updates);
    for (const subscriber of subscribers) {
      subscriber();
    }
  }

  function readSavedRefresh() {
    if (!storage) {
      return null;
    }
    try {
      const saved = storage.getItem(REFRESH_STORAGE_KEY);
      return isTokenString(saved) ? saved : null;
    } catch {
      storageAvailable = false;
      return null;
    }
  }

  function saveRefresh(token) {
    if (!storage) {
      return;
    }
    try {
      if (token) {
        storage.setItem(REFRESH_STORAGE_KEY, token);
      } else {
        storage.removeItem(REFRESH_STORAGE_KEY);
      }
      storageAvailable = true;
    } catch {
      storageAvailable = false;
    }
  }

  function assertCurrent(context) {
    if (current !== context) {
      throw new ApiError(0, 'stale-session');
    }
  }

  function retire() {
    const previous = current;
    current = createContext();
    previous.controller.abort();
    saveRefresh(null);
    return previous;
  }

  function expire(context) {
    assertCurrent(context);
    const error = new ApiError(401, 'session_expired');
    retire();
    publish('anonymous', { error });
    return error;
  }

  function acceptTokens(context, tokens) {
    if (!isTokenString(tokens?.access_token) || !isTokenString(tokens?.refresh_token)) {
      throw new ApiError(200, 'invalid-response');
    }
    context.accessToken = tokens.access_token;
    context.refreshToken = tokens.refresh_token;
    // A retired generation keeps the latest refresh only so logout can revoke it.
    assertCurrent(context);
    saveRefresh(context.refreshToken);
    if (snapshot.phase === 'authenticated' && snapshot.storageAvailable !== storageAvailable) {
      publish('authenticated', {
        permissions: snapshot.permissions,
        actorId: snapshot.actorId,
        error: snapshot.error,
      });
    }
  }

  function refreshAccess(context) {
    assertCurrent(context);
    if (!context.refreshToken) {
      throw new ApiError(401);
    }
    if (!context.refresh) {
      context.refresh = performRefresh(context).finally(() => { context.refresh = null; });
    }
    return context.refresh;
  }

  async function performRefresh(context) {
    try {
      const tokens = await api.refresh(context.refreshToken);
      acceptTokens(context, tokens);
    } catch (error) {
      assertCurrent(context);
      const failure = safeError(error);
      if (failure.status === 401) {
        throw expire(context);
      }
      throw failure;
    }
  }

  async function read(context, path, externalSignal) {
    assertCurrent(context);
    const signal = contextSignal(context, externalSignal);
    const accessAtStart = context.accessToken;

    async function send(accessToken) {
      signal.throwIfAborted();
      try {
        const response = await api.get(path, { accessToken, signal });
        assertCurrent(context);
        signal.throwIfAborted();
        return response;
      } catch (error) {
        assertCurrent(context);
        signal.throwIfAborted();
        throw safeError(error);
      }
    }

    try {
      return await send(accessAtStart);
    } catch (error) {
      if (error?.status !== 401) {
        throw error;
      }
    }

    // A late 401 for the old access token can use a rotation that already succeeded.
    if (context.accessToken === accessAtStart) {
      await refreshAccess(context);
    }
    assertCurrent(context);
    const accessAtRetry = context.accessToken;
    try {
      return await send(accessAtRetry);
    } catch (error) {
      if (error?.status === 401 && current === context && context.accessToken === accessAtRetry) {
        const expired = expire(context);
        void revoke(context);
        throw expired;
      }
      throw error;
    }
  }

  async function loadPermissions(context, revision = context.permissionRevision) {
    const data = await read(context, PERMISSIONS_PATH);
    assertCurrent(context);
    if (revision !== context.permissionRevision) {
      return false;
    }
    if (!Array.isArray(data?.permissions) ||
        data.permissions.some((permission) => typeof permission !== 'string' || permission.length === 0)) {
      throw new ApiError(200, 'invalid-response');
    }
    const permissions = Object.freeze([...new Set(data.permissions)]);
    if (snapshot.permissions.includes(TICKET_VIEW) && !permissions.includes(TICKET_VIEW)) {
      context.permissionRevision += 1;
    }
    publish('authenticated', {
      permissions,
      actorId: actorIdFromToken(context.accessToken),
    });
    return true;
  }

  function withdrawTicketView(context, error) {
    context.permissionRevision += 1;
    publish('authenticated', {
      permissions: Object.freeze(snapshot.permissions.filter((permission) => permission !== TICKET_VIEW)),
      actorId: snapshot.actorId,
      error,
    });
  }

  async function bootstrap(context, loadTokens) {
    try {
      await loadTokens();
      return await loadPermissions(context);
    } catch (error) {
      if (current === context) {
        const phase = context.refreshToken ? 'error' : 'anonymous';
        publish(phase, { error: safeError(error) });
      }
      return false;
    } finally {
      context.bootstrap = null;
    }
  }

  function reloadPermissions(context) {
    assertCurrent(context);
    if (context.bootstrap) {
      return context.bootstrap;
    }
    if (!context.accessToken) {
      return Promise.resolve(false);
    }
    const revision = context.permissionRevision;
    if (context.permissions?.revision !== revision) {
      const request = { revision, promise: null };
      request.promise = loadPermissions(context, revision)
        .catch((error) => {
          if (current === context && context.permissionRevision === revision) {
            const failure = safeError(error);
            if (failure.status === 403 || snapshot.phase !== 'authenticated') {
              context.permissionRevision += 1;
              publish('error', { error: failure });
            } else {
              publish('authenticated', {
                permissions: snapshot.permissions,
                actorId: snapshot.actorId,
                error: failure,
              });
            }
          }
          return false;
        })
        .finally(() => {
          if (context.permissions === request) {
            context.permissions = null;
          }
        });
      context.permissions = request;
    }
    return context.permissions.promise;
  }

  async function revoke(context) {
    await Promise.allSettled([context.login, context.refresh]);
    const token = context.refreshToken;
    context.accessToken = null;
    context.refreshToken = null;
    if (!token) {
      return 'none';
    }
    try {
      await api.logout(token);
      return 'revoked';
    } catch {
      return 'unconfirmed';
    }
  }

  return {
    getSnapshot: () => snapshot,

    subscribe(subscriber) {
      subscribers.add(subscriber);
      return () => subscribers.delete(subscriber);
    },

    restore() {
      if (snapshot.phase === 'authenticated') {
        return Promise.resolve(true);
      }
      if (current.bootstrap) {
        return current.bootstrap;
      }
      if (!current.refreshToken) {
        return Promise.resolve(false);
      }
      const context = current;
      context.bootstrap = bootstrap(context, async () => {
        if (!context.accessToken) {
          await refreshAccess(context);
        }
      });
      publish('restoring');
      return context.bootstrap;
    },

    login(username, password) {
      void revoke(retire());
      const context = current;
      async function loginAndAccept() {
        const tokens = await api.login(username, password);
        acceptTokens(context, tokens);
      }
      context.login = loginAndAccept().finally(() => { context.login = null; });
      context.bootstrap = bootstrap(context, () => context.login);
      publish('authenticating');
      return context.bootstrap;
    },

    reloadPermissions: () => reloadPermissions(current),

    bindSignal: (signal) => contextSignal(current, signal),

    async logout() {
      const previous = retire();
      const context = current;
      publish('anonymous', {
        logoutStatus: previous.refreshToken || previous.bootstrap ? 'pending' : 'none',
      });
      const status = await revoke(previous);
      if (current === context) {
        publish('anonymous', { logoutStatus: status });
      }
      return status;
    },

    async get(path, { signal } = {}) {
      const context = current;
      if (snapshot.phase !== 'authenticated') {
        throw new ApiError(401);
      }
      const readsTicket = /^\/admin\/tickets(?:[/?]|$)/.test(path);
      if (readsTicket && !snapshot.permissions.includes(TICKET_VIEW)) {
        throw new ApiError(403);
      }
      const revision = context.permissionRevision;
      let data;
      try {
        data = await read(context, path, signal);
      } catch (error) {
        if (current !== context && error?.code !== 'session_expired') {
          assertCurrent(context);
        }
        if (readsTicket && context.permissionRevision !== revision) {
          throw new ApiError(0, 'stale-permissions');
        }
        if (error?.status === 403 && current === context && path !== PERMISSIONS_PATH) {
          if (readsTicket) {
            withdrawTicketView(context, error);
          } else {
            await reloadPermissions(context);
            assertCurrent(context);
          }
        }
        throw error;
      }
      assertCurrent(context);
      signal?.throwIfAborted();
      if (readsTicket && context.permissionRevision !== revision) {
        throw new ApiError(0, 'stale-permissions');
      }
      return data;
    },

    async mutate(path, { method, json, idempotencyKey, signal } = {}) {
      const context = current;
      if (snapshot.phase !== 'authenticated') {
        throw new ApiError(401);
      }
      const activeSignal = contextSignal(context, signal);
      activeSignal.throwIfAborted();
      try {
        const data = await api.mutate(path, {
          method, json, idempotencyKey, accessToken: context.accessToken, signal: activeSignal,
        });
        assertCurrent(context);
        activeSignal.throwIfAborted();
        return data;
      } catch (error) {
        assertCurrent(context);
        activeSignal.throwIfAborted();
        throw safeError(error);
      }
    },
  };
}
