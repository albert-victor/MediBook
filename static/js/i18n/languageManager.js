/**
 * mediBook i18n - language loading, persistence, DOM application
 */

import { setMessages, getLocale, t } from "./translator.js";

export const STORAGE_KEY = "medcare_lang";
export const DEFAULT_LOCALE = "en";
export const SUPPORTED_LOCALES = ["en", "sw"];
export const LOCALE_LABELS = {
  en: { short: "EN", full: "English", flag: "🇬🇧" },
  sw: { short: "SW", full: "Kiswahili", flag: "🇹🇿" },
};

const LOCALE_PATH = "/static/js/i18n/locales";
const cache = new Map();
let currentLocale = DEFAULT_LOCALE;
let initialized = false;

/** @type {Set<(locale: string) => void>} */
const listeners = new Set();

/**
 * @param {(locale: string) => void} fn
 * @returns {() => void}
 */
export function onLanguageChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function notifyListeners() {
  listeners.forEach((fn) => {
    try {
      fn(currentLocale);
    } catch (err) {
      console.error("[i18n] listener error", err);
    }
  });
  document.dispatchEvent(
    new CustomEvent("medcare:languagechange", { detail: { locale: currentLocale } })
  );
}

/**
 * @param {string} locale
 */
export async function loadLocale(locale) {
  const code = SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE;
  if (cache.has(code)) return cache.get(code);

  const response = await fetch(`${LOCALE_PATH}/${code}.json`);
  if (!response.ok) throw new Error(`Failed to load locale: ${code}`);
  const data = await response.json();
  cache.set(code, data);
  return data;
}

/**
 * Apply translations to static DOM elements (preserves nodes - no animation reset).
 */
export function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    if (el.hasAttribute("data-i18n-skip")) return;
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    let vars = {};
    const params = el.getAttribute("data-i18n-params");
    if (params) {
      try {
        vars = JSON.parse(params);
      } catch {
        /* ignore invalid JSON */
      }
    }
    const value = t(key, vars);
    if (value && value !== key) el.textContent = value;
  });

  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = el.getAttribute("data-i18n-html");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) el.innerHTML = value;
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) el.setAttribute("placeholder", value);
  });

  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    const key = el.getAttribute("data-i18n-aria");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) el.setAttribute("aria-label", value);
  });

  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    const key = el.getAttribute("data-i18n-title");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) el.setAttribute("title", value);
  });

  document.documentElement.lang = currentLocale === "sw" ? "sw" : "en";
  document.documentElement.setAttribute("data-locale", currentLocale);

  updateSwitcherUI();
}

function updateSwitcherUI() {
  document.querySelectorAll("[data-lang-switch]").forEach((btn) => {
    const locale = btn.getAttribute("data-lang-switch");
    const isActive = locale === currentLocale;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-pressed", String(isActive));
  });
}

/**
 * @param {string} locale
 * @param {{ silent?: boolean, force?: boolean }} [options]
 */
export async function setLanguage(locale, options = {}) {
  const code = SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE;
  if (code === currentLocale && initialized && !options.force) return;

  const messages = await loadLocale(code);
  currentLocale = code;
  setMessages(code, messages);
  localStorage.setItem(STORAGE_KEY, code);
  applyTranslations();
  if (!options.silent) notifyListeners();
}

/** @returns {string} */
export function getCurrentLanguage() {
  return currentLocale;
}

function bindSwitcher() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-lang-switch]");
    if (!btn) return;
    e.preventDefault();
    const locale = btn.getAttribute("data-lang-switch");
    if (locale) setLanguage(locale);
  });
}

/**
 * Initialize i18n - auto-started on module load; await `i18nReady` in page scripts.
 */
export async function initI18n() {
  await i18nReady;
  bindSwitcher();
  const run = () => {
    applyTranslations();
    initialized = true;
    notifyListeners();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
  } else {
    run();
  }
}

const stored = localStorage.getItem(STORAGE_KEY);
const preferred = SUPPORTED_LOCALES.includes(stored) ? stored : DEFAULT_LOCALE;

/** Resolves when locale messages are loaded (before DOM apply). */
export const i18nReady = loadLocale(preferred).then((messages) => {
  currentLocale = preferred;
  setMessages(preferred, messages);
});

initI18n();

export { getLocale, t };
