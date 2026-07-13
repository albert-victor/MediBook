/**
 * Careers doctor application form - client-side validation
 */

import { t } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";

const PASSWORD_MIN = 8;
const PHONE_RE = /^\+?[\d\s\-()]{9,20}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const RULES = {
  first_name: { required: true, minLength: 2 },
  last_name: { required: true, minLength: 2 },
  email: { required: true, email: true },
  phone: { phone: true, optional: true },
  password: { required: true, password: true },
  confirm_password: { required: true, match: "password" },
  specialization_id: { required: true },
  license_number: { required: true, minLength: 3 },
  hospital_name: { required: true, minLength: 2 },
  consultation_fee: { required: true, number: true, min: 0 },
  experience_years: { number: true, optional: true, min: 0 },
  terms_accepted: { required: true, checkbox: true },
};

function validatePassword(value) {
  if (value.length < PASSWORD_MIN) return t("auth.validation.passwordMin", { count: PASSWORD_MIN });
  if (!/[A-Z]/.test(value)) return t("auth.validation.passwordUpper");
  if (!/[a-z]/.test(value)) return t("auth.validation.passwordLower");
  if (!/\d/.test(value)) return t("auth.validation.passwordNumber");
  return null;
}

function validateField(name, value, rules, form) {
  const rule = rules[name];
  if (!rule) return null;

  const trimmed = typeof value === "string" ? value.trim() : value;

  if (rule.optional && (!trimmed || trimmed === "")) return null;

  if (rule.checkbox) {
    const input = form.querySelector(`[name="${name}"]`);
    if (rule.required && !input?.checked) return t("auth.validation.required");
    return null;
  }

  if (rule.required && (!trimmed || trimmed === "")) return t("auth.validation.required");

  if (rule.email && trimmed && !EMAIL_RE.test(trimmed)) return t("auth.validation.email");
  if (rule.phone && trimmed && !PHONE_RE.test(trimmed)) return t("auth.validation.phone");
  if (rule.minLength && trimmed.length < rule.minLength) {
    return t("auth.validation.minLength", { count: rule.minLength });
  }
  if (rule.password) {
    const pwErr = validatePassword(trimmed);
    if (pwErr) return pwErr;
  }
  if (rule.match) {
    const other = form.querySelector(`[name="${rule.match}"]`)?.value ?? "";
    if (trimmed !== other) return t("auth.validation.passwordMismatch");
  }
  if (rule.number && trimmed !== "") {
    const num = Number(trimmed);
    if (Number.isNaN(num)) return t("auth.validation.required");
    if (rule.min !== undefined && num < rule.min) return t("auth.validation.required");
  }

  return null;
}

function showFieldError(group, message) {
  group.classList.add("med-form-group--invalid");
  let err = group.querySelector(".med-form-error");
  if (!err) {
    err = document.createElement("span");
    err.className = "med-form-error";
    err.setAttribute("role", "alert");
    err.innerHTML = '<i class="bi bi-exclamation-circle"></i> ';
    group.appendChild(err);
  }
  err.lastChild.textContent = message ? ` ${message}` : "";
  const input = group.querySelector(".med-input, .med-select, .med-check__input");
  input?.classList.add("med-input--error");
}

function clearFieldError(group) {
  group.classList.remove("med-form-group--invalid");
  group.querySelector(".med-form-error")?.remove();
  group.querySelector(".med-input--error")?.classList.remove("med-input--error");
}

function validateForm(form) {
  let valid = true;
  Object.keys(RULES).forEach((name) => {
    const group = form.querySelector(`[data-field="${name}"]`);
    if (!group) return;
    clearFieldError(group);
    const input = group.querySelector(`[name="${name}"]`);
    const value = RULES[name].checkbox ? null : (input?.value ?? "");
    const error = validateField(name, value, RULES, form);
    if (error) {
      showFieldError(group, error);
      valid = false;
    }
  });
  return valid;
}

function bindForm(form) {
  form.addEventListener("submit", (e) => {
    if (!validateForm(form)) e.preventDefault();
  });

  form.querySelectorAll("[data-validate]").forEach((input) => {
    input.addEventListener("blur", () => {
      const name = input.name;
      const group = form.querySelector(`[data-field="${name}"]`);
      if (!group) return;
      clearFieldError(group);
      const error = validateField(name, input.type === "checkbox" ? null : input.value, RULES, form);
      if (error) showFieldError(group, error);
    });
  });
}

function init() {
  const form = document.querySelector("[data-careers-form]");
  if (form) bindForm(form);
}

i18nReady.then(init);
onLanguageChange(init);
