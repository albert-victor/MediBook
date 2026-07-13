/**
 * mediBook Toast - slide-in notification system
 */

import { t } from "../i18n/translator.js";

const ICONS = {
  success: "bi-check-circle-fill",
  error: "bi-x-circle-fill",
  warning: "bi-exclamation-triangle-fill",
  info: "bi-info-circle-fill",
};

let container = null;

function getContainer(position = "top-right") {
  if (!container) {
    container = document.createElement("div");
    container.className = "med-toast-container";
    if (position === "bottom-right") {
      container.classList.add("med-toast-container--bottom");
    }
    document.body.appendChild(container);
  }
  return container;
}

/**
 * Show a toast notification.
 * @param {Object} options
 * @param {string} options.type - success | error | warning | info
 * @param {string} options.title
 * @param {string} [options.message]
 * @param {number} [options.duration=5000] - ms, 0 = no auto-dismiss
 */
export function showToast({ type = "info", title, message = "", duration = 5000 }) {
  const el = document.createElement("div");
  el.className = `med-toast med-toast--${type}`;
  el.setAttribute("role", "alert");

  el.innerHTML = `
    <span class="med-toast__icon"><i class="bi ${ICONS[type] || ICONS.info}"></i></span>
    <div class="med-toast__content">
      <div class="med-toast__title">${title}</div>
      ${message ? `<div class="med-toast__message">${message}</div>` : ""}
    </div>
    <button class="med-toast__close" aria-label="${t("common.dismiss")}">
      <i class="bi bi-x"></i>
    </button>
    ${duration > 0 ? `<div class="med-toast__progress"><div class="med-toast__progress-bar" style="animation-duration:${duration}ms"></div></div>` : ""}
  `;

  const dismiss = () => {
    el.classList.add("is-leaving");
    el.addEventListener("animationend", () => el.remove(), { once: true });
  };

  el.querySelector(".med-toast__close").addEventListener("click", dismiss);

  getContainer().appendChild(el);

  if (duration > 0) {
    setTimeout(dismiss, duration);
  }

  return { dismiss };
}

export const toast = {
  success: (title, message) => showToast({ type: "success", title, message }),
  error:   (title, message) => showToast({ type: "error", title, message }),
  warning: (title, message) => showToast({ type: "warning", title, message }),
  info:    (title, message) => showToast({ type: "info", title, message }),
};
