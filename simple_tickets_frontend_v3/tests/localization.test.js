import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  applyMessages, DEFAULT_LOCALE, errorKey, errorText, getMessageRevision, locale,
  referenceMessages, renderMessage, subscribeMessages, t, validateDictionary, validateLanguageCatalog,
} from '../src/shared/i18n/messages.js';

const options = [
  { id: 'ru-RU', label: 'Русский' },
  { id: 'en-US', label: '  English  ' },
  { id: 'zh-Hant', label: '繁體中文' },
];
const catalog = { version: 1, defaultLanguage: 'ru-RU', languages: options };
const dict = (messages, language = 'en-US') => ({ version: 1, language, messages });

test('catalog accepts canonical language IDs and labels as text', () => {
  const config = validateLanguageCatalog(catalog);
  assert.deepEqual(config, {
    defaultLanguage: 'ru-RU',
    languages: [options[0], { ...options[1], label: 'English' }, options[2]],
  });
  assert.ok(Object.isFrozen(config.languages[0]));
  assert.equal(validateLanguageCatalog({
    ...catalog, languages: [...options, { id: 'de-DE', label: '<b>Deutsch</b>' }],
  }).languages.at(-1).label, '<b>Deutsch</b>');
});

test('catalog rejects alternate paths, duplicate IDs and invalid metadata', () => {
  for (const id of ['EN-us', '..', '../dict', 'en_US', 'en-US.json', '__proto__', 'https://example.invalid/en-US']) {
    assert.equal(validateLanguageCatalog({ ...catalog, languages: [...options, { id, label: 'Invalid' }] }), null);
  }
  const oversizedId = "en-Latn-US-u-ca-gregory-co-phonebk-cu-usd-hc-h23-kf-upper-kn-nu-latn";
  assert.equal(validateLanguageCatalog({ ...catalog, languages: [...options, { id: oversizedId, label: 'Too long' }] }), null);
  for (const raw of [
    { ...catalog, version: 2 },
    { ...catalog, defaultLanguage: 'de-DE' },
    { ...catalog, languages: [...options, options[0]] },
    { ...catalog, languages: [{ id: 'ru-RU', label: ' ' }] },
    { ...catalog, languages: [{ id: 'ru-RU', label: 'Русский', url: 'https://example.invalid/' }] },
    { ...catalog, url: 'https://example.invalid/' },
    { ...catalog, languages: [] },
    Object.assign(Object.create({ foreign: true }), catalog),
  ]) {
    assert.equal(validateLanguageCatalog(raw), null);
  }
});

test('dictionary validates only known string values and rejects unsafe or missing placeholders per key', () => {
  const candidates = JSON.parse('{"__proto__":{"polluted":true},"constructor":"unsafe","queue.someNewKey":"unimplemented"}');
  Object.assign(candidates, {
    'login.submit': 'Sign in',
    'queue.range': '{total} total; {start} to {end}',
    'queue.activeStatus': 'Status {value}',
    'queue.activeSearch': 'Bad {query}',
    'queue.filtersCount': 'Filters',
    'common.identifier': 'Ticket {{id}}',
    'work.tabLabel': 'Unknown {id} {title} {extra}',
    'directory.action.remove.help': 'Bad {name} {id.secret}',
    'common.retry': ' ',
    'login.username': ['Not a string'],
  });

  const messages = validateDictionary(dict(candidates), 'en-US');
  assert.deepEqual({ ...messages }, {
    'login.submit': 'Sign in',
    'queue.range': '{total} total; {start} to {end}',
    'queue.activeStatus': 'Status {value}',
  });
  assert.ok(Object.isFrozen(messages));
  assert.equal(Object.getPrototypeOf(messages), null);
  assert.equal({}.polluted, undefined);
});

test('dictionary rejects a foreign locale, wrong version, array, prototype, or package URL', () => {
  for (const raw of [
    dict({}, 'ru-RU'),
    dict([]),
    dict(Object.create({ 'login.submit': 'Inherited' })),
    { ...dict({}), version: '1' },
    { ...dict({}), path: 'https://example.invalid/' },
  ]) {
    assert.equal(validateDictionary(raw, 'en-US'), null);
  }
  assert.equal(validateDictionary(dict({}, 'en_us'), 'en_us'), null);
});

test('active translations publish one revision and keep fallback text for missing or malformed keys', (context) => {
  const received = [];
  const stop = subscribeMessages(() => received.push(getMessageRevision()));
  context.after(() => {
    stop();
    applyMessages(DEFAULT_LOCALE, null);
  });

  const initialRevision = getMessageRevision();
  const candidate = {
    'login.submit': 'Sign in',
    'queue.range': '{start} to {end} of {total}',
    'common.identifier': 'Unknown {number}',
  };
  assert.equal(applyMessages('en-US', candidate), true);
  assert.equal(locale, 'en-US');
  assert.equal(t('login.submit'), 'Sign in');
  assert.equal(t('queue.range', { start: 1, end: 10, total: 42 }), '1 to 10 of 42');
  assert.equal(t('common.identifier', { id: 7 }), '№ 7');
  assert.equal(t('queue.title'), referenceMessages['queue.title']);
  assert.deepEqual(received, [initialRevision + 1]);
  assert.equal(applyMessages('en-US', { ...candidate }), false);
  candidate['login.submit'] = 'Changed after dispatch';
  assert.equal(t('login.submit'), 'Sign in');

  assert.equal(applyMessages(DEFAULT_LOCALE, { 'login.submit': 'Начать сеанс' }), true);
  assert.equal(locale, DEFAULT_LOCALE);
  assert.equal(t('login.submit'), 'Начать сеанс');
  stop();
  applyMessages('../unsafe', { 'login.submit': 'Invalid' });
  assert.equal(t('login.submit'), referenceMessages['login.submit']);
  assert.deepEqual(received, [initialRevision + 1, initialRevision + 2]);
});

test('message descriptors and errors are translated when rendered', (context) => {
  context.after(() => applyMessages(DEFAULT_LOCALE, null));
  const queued = { key: 'directory.action.remove.help', params: { name: '<profile>', id: 1 } };
  const timeout = { key: errorKey({ code: 'timeout', status: 0 }) };
  assert.equal(renderMessage('Текст пользователя'), 'Текст пользователя');
  applyMessages('en-US', {
    'directory.action.remove.help': 'Remove {name} ({id})?',
    'error.timeout': 'The request timed out.',
  });
  assert.equal(renderMessage(queued), 'Remove <profile> (1)?');
  assert.equal(renderMessage(timeout), 'The request timed out.');
  assert.equal(errorText({ code: 'timeout', status: 0 }), 'The request timed out.');
  assert.equal(t('common.identifier', Object.create({ id: 'inherited' })), '№ {id}');
  assert.equal(renderMessage(null), '');
});

test('published Russian dictionary carries the complete bundled operator reference', async () => {
  const metadata = JSON.parse(await readFile(new URL('../public/config/locales.json', import.meta.url), 'utf8'));
  const published = JSON.parse(await readFile(new URL('../public/config/locales/ru-RU.json', import.meta.url), 'utf8'));
  const reference = validateDictionary(published, DEFAULT_LOCALE);
  assert.equal(validateLanguageCatalog(metadata)?.defaultLanguage, DEFAULT_LOCALE);
  assert.ok(reference);
  assert.deepEqual(Object.keys(reference).sort(), Object.keys(referenceMessages).sort());
});
