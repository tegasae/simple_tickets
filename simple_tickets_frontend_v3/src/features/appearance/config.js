const configPath = /^\/config\/(?:themes\.json|locales\.json|locales\/[A-Za-z0-9-]{2,63}\.json)$/;
const maximumSize = 256 * 1024;

export function isAppearanceConfigPath(path) {
  return typeof path === "string" && configPath.test(path);
}

async function readJson(response) {
  const reader = response.body?.getReader();
  if (!reader) return null;
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let size = 0;
  let raw = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return JSON.parse(raw + decoder.decode());
      size += value.byteLength;
      if (size > maximumSize) return null;
      raw += decoder.decode(value, { stream: true });
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function readAppearanceConfig(path, { signal, fetchImpl = globalThis.fetch } = {}) {
  if (!isAppearanceConfigPath(path)) return null;
  const timeout = AbortSignal.timeout(5_000);
  const requestSignal = signal ? AbortSignal.any([signal, timeout]) : timeout;
  try {
    const response = await fetchImpl(path, {
      headers: { Accept: "application/json" },
      credentials: "omit",
      referrerPolicy: "no-referrer",
      redirect: "error",
      cache: "no-store",
      signal: requestSignal,
    });
    if (!response.ok || !/^application\/json(?:\s*;|$)/i.test(response.headers.get("content-type") ?? "") ||
        Number(response.headers.get("content-length")) > maximumSize) {
      await response.body?.cancel().catch(() => {});
      return null;
    }
    return await readJson(response);
  } catch {
    return null;
  }
}
