import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { readAppearanceConfig } from "../src/features/appearance/config.js";
import { applyTheme, classicTheme, selectTheme, validateThemeCatalog } from "../src/features/appearance/theme.js";

const shipped = JSON.parse(await readFile(new URL("../public/config/themes.json", import.meta.url), "utf8"));

test("the four v2 themes are shipped as public configuration and selected by stable ID", () => {
  const catalog = validateThemeCatalog(shipped);
  assert.deepEqual(new Set(catalog.themes.map(({ id }) => id)), new Set(["onec", "classic", "futuristic", "barbie"]));
  assert.equal(selectTheme(catalog, "futuristic").tokens["--scheme"], "dark");
  assert.equal(selectTheme(catalog, "removed").id, "classic");
  assert.equal(selectTheme(null, "futuristic"), classicTheme);
});

test("theme validation rejects duplicate IDs, unsafe CSS and ambiguous defaults", () => {
  const custom = { id: "lagoon", label: "Lagoon", tokens: { "--accent": "#224466", "--control-height": "56px" } };
  const catalog = { version: 1, defaultTheme: custom.id, themes: [custom] };
  assert.equal(validateThemeCatalog(catalog).themes[0].tokens["--control-height"], "56px");
  assert.equal(validateThemeCatalog({ ...catalog, defaultTheme: "missing" }), null);
  assert.equal(validateThemeCatalog({ ...catalog, themes: [custom, custom] }), null);
  assert.equal(validateThemeCatalog({ ...catalog, themes: [{ ...custom, id: "../lagoon" }] }), null);
  for (const tokens of [{ "--accent": "url(https://example.invalid)" }, { "--injected": "#112233" },
    { "--scheme": "normal dark" }, { "--radius": "25px" }, { "--control-height": "0px" },
    JSON.parse('{"--accent":"#112233","__proto__":{}}')]) {
    assert.equal(validateThemeCatalog({ ...catalog, themes: [{ ...custom, tokens }] }), null);
  }
});

test("changing theme clears inline values from the previous preset", () => {
  const properties = new Map();
  const root = { dataset: {}, style: {
    setProperty: (name, value) => properties.set(name, value),
    removeProperty: (name) => properties.delete(name),
  } };
  applyTheme(root, selectTheme(validateThemeCatalog(shipped), "barbie"));
  assert.equal(root.dataset.theme, "barbie");
  assert.ok(properties.size > 0);
  const subset = { id: "lagoon", tokens: { "--accent": "#224466" } };
  applyTheme(root, subset);
  assert.deepEqual([...properties], [["--accent", "#224466"]]);
  applyTheme(root, classicTheme);
  assert.equal(root.dataset.theme, "classic");
  assert.equal(properties.size, 0);
});

test("appearance GET is credential-free and rejects foreign paths and non-JSON responses", async () => {
  let requests = 0;
  const fetchImpl = (path, options) => {
    requests += 1;
    assert.equal(path, "/config/locales/en-US.json");
    assert.equal(options.credentials, "omit");
    assert.equal(options.referrerPolicy, "no-referrer");
    assert.equal(options.redirect, "error");
    assert.equal(options.cache, "no-store");
    assert.deepEqual(options.headers, { Accept: "application/json" });
    return Response.json({ version: 1 });
  };
  assert.deepEqual(await readAppearanceConfig("/config/locales/en-US.json", { fetchImpl }), { version: 1 });
  assert.equal(await readAppearanceConfig("https://foreign.invalid/config/themes.json", { fetchImpl }), null);
  assert.equal(await readAppearanceConfig("/config/locales/../themes.json", { fetchImpl }), null);
  assert.equal(requests, 1);
  assert.equal(await readAppearanceConfig("/config/themes.json", {
    fetchImpl: () => new Response("<html>", { headers: { "Content-Type": "text/html" } }),
  }), null);
  assert.equal(await readAppearanceConfig("/config/themes.json", {
    fetchImpl: () => new Response('"' + "я".repeat(140_000) + '"', { headers: { "Content-Type": "application/json" } }),
  }), null);
});
