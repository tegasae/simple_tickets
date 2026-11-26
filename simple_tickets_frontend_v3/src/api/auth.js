const AUTH_PREFIX = '/auth/admin';

export function isTokenString(value) {
  return typeof value === 'string' && /^[!-~]+$/.test(value);
}

function isTokenResponse(value) {
  return value !== null &&
    typeof value === 'object' &&
    isTokenString(value.access_token) &&
    isTokenString(value.refresh_token) &&
    typeof value.token_type === 'string' &&
    value.token_type.toLowerCase() === 'bearer' &&
    Number.isInteger(value.expires_in) &&
    value.expires_in >= 0 &&
    typeof value.scope === 'string';
}

export function createAuth(request) {
  return {
    login(username, password, { signal } = {}) {
      return request(`${AUTH_PREFIX}/login`, {
        method: 'POST',
        body: new URLSearchParams({ username, password }),
        signal,
        validate: isTokenResponse,
      });
    },

    refresh(refreshToken, { signal } = {}) {
      return request(`${AUTH_PREFIX}/refresh`, {
        method: 'POST',
        json: { refresh_token: refreshToken },
        signal,
        validate: isTokenResponse,
      });
    },

    logout(refreshToken, { signal } = {}) {
      return request(`${AUTH_PREFIX}/logout`, {
        method: 'POST',
        json: { refresh_token: refreshToken },
        signal,
        validate: (value) => value !== null &&
          typeof value === 'object' &&
          typeof value.message === 'string',
      });
    },
  };
}
