/**
 * mediBook i18n - translation lookup and interpolation
 */

let _messages = {};
let _locale = "en";

/**
 * Load messages object for a locale (called by languageManager).
 * @param {string} locale
 * @param {Record<string, unknown>} messages
 */
export function setMessages(locale, messages) {
  _locale = locale;
  _messages = messages || {};
}

/** @returns {string} */
export function getLocale() {
  return _locale;
}

/**
 * Resolve nested key (e.g. "navigation.home").
 * @param {string} key
 * @param {Record<string, unknown>} [source]
 * @returns {string|undefined}
 */
export function resolveKey(key, source = _messages) {
  if (!key) return undefined;
  const parts = key.split(".");
  let current = source;
  for (const part of parts) {
    if (current == null || typeof current !== "object") return undefined;
    current = current[part];
  }
  return typeof current === "string" ? current : undefined;
}

/**
 * Translate a key with optional variable interpolation.
 * Variables: t("greeting", { name: "Amina" }) → "Hello, Amina"
 * @param {string} key
 * @param {Record<string, string|number>} [vars]
 * @param {string} [fallback]
 * @returns {string}
 */
export function t(key, vars = {}, fallback = "") {
  let text = resolveKey(key) ?? fallback ?? key;
  if (vars && typeof text === "string") {
    text = text.replace(/\{(\w+)\}/g, (_, name) =>
      vars[name] !== undefined ? String(vars[name]) : `{${name}}`
    );
  }
  return text;
}

/**
 * Translate API / backend message if a mapping key exists.
 * @param {string} message
 * @returns {string}
 */
export function tApiMessage(message) {
  if (!message) return "";

  const LEGACY = {
    "Not authenticated": "api.unauthorized",
    "Patients only": "api.patientsOnly",
    "Doctors only": "api.doctorsOnly",
    "Admins only": "api.adminsOnly",
    "Request failed": "api.requestFailed",
    "Appointment not found": "api.appointmentNotFound",
    "Doctor not found": "api.notFound",
    "Notification not found": "api.notFound",
    "This appointment slot has already been booked. Please choose another available time.": "booking.slotConflict",
    "A user with this email already exists": "api.emailExists",
    "License number already registered": "api.licenseExists",
  };

  const mapped = LEGACY[message];
  if (mapped) {
    const translated = resolveKey(mapped);
    if (translated) return translated;
  }

  const direct = resolveKey(`api.${message}`);
  if (direct) return direct;

  return message;
}

/**
 * Map server greeting strings to localized greetings.
 * @param {string} greeting
 */
export function translateGreeting(greeting) {
  const map = {
    "Good morning": "common.goodMorning",
    "Good afternoon": "common.goodAfternoon",
    "Good evening": "common.goodEvening",
    "Welcome back": "common.welcomeBack",
  };
  const key = map[greeting];
  return key ? t(key) : greeting;
}

/**
 * Locale-aware date formatting (does not translate month names via i18n - uses Intl).
 * @param {string|Date} value
 * @param {Intl.DateTimeFormatOptions} [options]
 */
export function formatDate(value, options = {}) {
  const d = value instanceof Date ? value : new Date(value);
  const locale = _locale === "sw" ? "sw-TZ" : "en-GB";
  return d.toLocaleDateString(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...options,
  });
}

/**
 * Locale-aware time formatting.
 * @param {string|Date} value
 * @param {Intl.DateTimeFormatOptions} [options]
 */
export function formatTime(value, options = {}) {
  const d = value instanceof Date ? value : new Date(value);
  const locale = _locale === "sw" ? "sw-TZ" : "en-GB";
  return d.toLocaleTimeString(locale, {
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  });
}

/**
 * Relative time ago string.
 * @param {string|Date} value
 */
export function timeAgo(value) {
  const diff = Date.now() - new Date(value).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return t("common.justNow");
  if (mins < 60) return t("common.minutesAgo", { count: mins });
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return t("common.hoursAgo", { count: hrs });
  const days = Math.floor(hrs / 24);
  if (days < 7) return t("common.daysAgo", { count: days });
  return formatDate(value);
}
