import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { applyMessages, DEFAULT_LOCALE, locale, validateDictionary, validateLanguageCatalog } from "../../shared/i18n/messages.js";
import { readAppearanceConfig } from "./config.js";
import { applyTheme, classicTheme, selectTheme, validateThemeCatalog } from "./theme.js";

const themePreference = "simple-tickets.v3.theme";
const languagePreference = "simple-tickets.v3.language";
const russian = Object.freeze({ id: DEFAULT_LOCALE, label: "Русский" });
const fallbackLanguages = Object.freeze([russian]);
const fallbackThemes = Object.freeze([classicTheme]);

function readPreference(key) {
  try { return window.localStorage.getItem(key); }
  catch { return null; }
}

function savePreference(key, value) {
  try { window.localStorage.setItem(key, value); }
  catch { /* The choice still works in the current page. */ }
}

export function useAppearance() {
  const [themeCatalog, setThemeCatalog] = useState(null);
  const [languageCatalog, setLanguageCatalog] = useState(null);
  const [savedTheme, setSavedTheme] = useState(() => readPreference(themePreference));
  const [languageChoice, setLanguageChoice] = useState(() => ({ id: readPreference(languagePreference), manual: false }));
  const [loadingLanguage, setLoadingLanguage] = useState(null);
  const [failedLanguage, setFailedLanguage] = useState(null);
  const dictionaryRequest = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;
    void readAppearanceConfig("/config/themes.json", { signal }).then((raw) => {
      if (!signal.aborted) setThemeCatalog(validateThemeCatalog(raw));
    });
    void readAppearanceConfig("/config/locales.json", { signal }).then((raw) => {
      if (!signal.aborted) setLanguageCatalog(validateLanguageCatalog(raw));
    });
    return () => controller.abort();
  }, []);

  const theme = selectTheme(themeCatalog, savedTheme);
  useLayoutEffect(() => { applyTheme(document.documentElement, theme); }, [theme]);

  useEffect(() => {
    if (!languageCatalog) return undefined;
    const published = languageCatalog.languages.some(({ id }) => id === languageChoice.id);
    if (!published && languageChoice.id === DEFAULT_LOCALE) {
      document.documentElement.lang = DEFAULT_LOCALE;
      applyMessages(DEFAULT_LOCALE, null);
      setLoadingLanguage(null);
      return undefined;
    }
    const requested = published ? languageChoice.id : languageCatalog.defaultLanguage;
    const controller = new AbortController();
    dictionaryRequest.current = controller;
    const { signal } = controller;
    const choice = languageChoice;
    if (choice.manual) setLoadingLanguage(requested);
    setFailedLanguage(null);
    void readAppearanceConfig(`/config/locales/${requested}.json`, { signal }).then((raw) => {
      if (signal.aborted) return;
      const messages = validateDictionary(raw, requested);
      document.documentElement.lang = messages ? requested : DEFAULT_LOCALE;
      applyMessages(messages ? requested : DEFAULT_LOCALE, messages);
      setLoadingLanguage(null);
      if (!messages && (choice.manual || requested !== DEFAULT_LOCALE)) setFailedLanguage(requested);
    });
    return () => controller.abort();
  }, [languageCatalog, languageChoice]);

  const publishedLanguages = languageCatalog?.languages ?? fallbackLanguages;
  const languages = publishedLanguages.some(({ id }) => id === DEFAULT_LOCALE) ? publishedLanguages : [...publishedLanguages, russian];
  const themes = themeCatalog?.themes ?? fallbackThemes;

  return {
    themes, theme: theme.id,
    languages, language: locale,
    selectedLanguage: loadingLanguage ?? locale,
    languagePending: loadingLanguage !== null,
    languageError: failedLanguage !== null,
    onThemeChange(id) {
      if (!themes.some((item) => item.id === id)) return;
      savePreference(themePreference, id);
      setSavedTheme(id);
    },
    onLanguageChange(id) {
      if (!languages.some((item) => item.id === id)) return;
      dictionaryRequest.current?.abort();
      savePreference(languagePreference, id);
      setFailedLanguage(null);
      setLanguageChoice({ id, manual: true });
    },
  };
}
