/**
 * Auth form - client-side validation (mirrors server rules)
 */

import { t } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";

const PASSWORD_MIN = 8;
const PHONE_RE = /^\+?[\d\s\-()]{9,20}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const RULES = {
  login: {
    email: { required: true, email: true },
    password: { required: true },
  },
  register: {
    first_name: { required: true, minLength: 2 },
    last_name: { required: true, minLength: 2 },
    email: { required: true, email: true },
    phone: { phone: true, optional: true },
    password: { required: true, password: true },
    confirm_password: { required: true, match: "password" },
    terms_accepted: { required: true, checkbox: true },
  },
  forgot: {
    email: { required: true, email: true },
  },
  reset: {
    password: { required: true, password: true },
    confirm_password: { required: true, match: "password" },
  },
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

  if (rule.required && rule.checkbox && !value) {
    return t("auth.validation.required");
  }

  if (rule.required && !rule.checkbox && !trimmed) {
    return t("auth.validation.required");
  }

  if (rule.email && trimmed && !EMAIL_RE.test(trimmed)) {
    return t("auth.validation.email");
  }

  if (rule.phone && trimmed && !PHONE_RE.test(trimmed)) {
    return t("auth.validation.phone");
  }

  if (rule.minLength && trimmed && trimmed.length < rule.minLength) {
    return t("auth.validation.minLength", { count: rule.minLength });
  }

  if (rule.password && trimmed) {
    const pwError = validatePassword(trimmed);
    if (pwError) return pwError;
  }

  if (rule.match && trimmed) {
    const matchField = form.querySelector(`[name="${rule.match}"]`);
    if (matchField && trimmed !== matchField.value) {
      return t("auth.validation.passwordMismatch");
    }
  }

  return null;
}

function showFieldError(group, message) {
  const input = group.querySelector("[data-validate]");
  let errorEl = group.querySelector(".med-form-error");

  if (message) {
    input?.classList.add("is-invalid");
    input?.classList.remove("is-valid");
    if (!errorEl) {
      errorEl = document.createElement("span");
      errorEl.className = "med-form-error";
      errorEl.setAttribute("role", "alert");
      group.appendChild(errorEl);
    }
    errorEl.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${message}`;
    errorEl.style.display = "flex";
  } else {
    input?.classList.remove("is-invalid");
    if (input?.value) input.classList.add("is-valid");
    if (errorEl) errorEl.style.display = "none";
  }
}

function validateForm(form) {
  const formType = form.dataset.authForm;
  const rules = RULES[formType];
  if (!rules) return true;

  let valid = true;

  Object.keys(rules).forEach((name) => {
    const group = form.querySelector(`[data-field="${name}"]`);
    if (!group) return;

    const field = form.querySelector(`[name="${name}"]`);
    const value = field?.type === "checkbox" ? field.checked : field?.value ?? "";
    const error = validateField(name, value, rules, form);
    showFieldError(group, error);
    if (error) valid = false;
  });

  return valid;
}

function revalidateVisibleForms() {
  document.querySelectorAll("[data-auth-form]").forEach((form) => {
    if (form.querySelector(".is-invalid, .med-form-error[style*='flex']")) {
      validateForm(form);
    }
  });
}

function initPasswordToggles() {
  document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.querySelector("i").className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
    });
  });
}

function resetAuthLoading() {
  const loader = document.getElementById("auth-loading");
  if (loader) loader.hidden = true;
  document.body.classList.remove("auth-page--loading");
  document.querySelectorAll("[data-auth-form].is-submitting").forEach((form) => {
    form.classList.remove("is-submitting");
  });
}

function initAuthForms() {
  document.querySelectorAll("[data-auth-form]").forEach((form) => {
    form.querySelectorAll("[data-validate]").forEach((field) => {
      field.addEventListener("blur", () => validateForm(form));
      field.addEventListener("input", () => {
        const group = field.closest("[data-field]");
        if (group?.querySelector(".med-form-error")?.style.display !== "none") {
          validateForm(form);
        }
      });
    });

    form.addEventListener("submit", (e) => {
      if (!validateForm(form)) {
        e.preventDefault();
        const firstInvalid = form.querySelector(".is-invalid");
        firstInvalid?.focus();
      } else {
        form.classList.add("is-submitting");
        const loader = document.getElementById("auth-loading");
        if (loader) {
          loader.hidden = false;
          document.body.classList.add("auth-page--loading");
        }
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  resetAuthLoading();
  initPasswordToggles();
  initAuthForms();
  onLanguageChange(revalidateVisibleForms);
});

window.addEventListener("pageshow", () => {
  resetAuthLoading();
});
