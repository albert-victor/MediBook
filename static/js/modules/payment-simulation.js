/**
 * Payment Simulation Module
 * Single modal for processing, then redirect to confirmation (no overlapping UI).
 */

import { openModal, closeModal } from "../core/modal.js";
import { t } from "../i18n/translator.js";

const DEFAULT_DURATION_MS = 4500;
const REDIRECT_DELAY_MS = 700;

/**
 * @param {Object} options
 * @param {string} options.methodLabel
 * @param {number} options.amount
 * @param {string} options.currency
 * @param {number} [options.durationMs=4500]
 * @param {() => Promise<any>} options.onInitiate
 * @param {() => Promise<any>} options.onComplete
 * @param {(result: any) => void} [options.onSuccess]
 */
export async function runPaymentSimulation({
  methodLabel,
  amount,
  currency,
  durationMs = DEFAULT_DURATION_MS,
  onInitiate,
  onComplete,
  onSuccess,
}) {
  const formattedAmount = `${currency} ${Math.round(amount).toLocaleString()}`;
  const modalEl = buildModalElement(methodLabel, formattedAmount);
  const backdrop = openModal(modalEl);

  const closeBtn = backdrop.querySelector(".med-modal__close");
  if (closeBtn) closeBtn.style.display = "none";

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) e.stopPropagation();
  });

  const progressBar = backdrop.querySelector(".pay-sim__progress-bar");
  const statusEl = backdrop.querySelector(".pay-sim__status");
  const bodyEl = backdrop.querySelector(".pay-sim__body");
  const titleEl = backdrop.querySelector(".med-modal__title");

  try {
    if (onInitiate) await onInitiate();
  } catch (err) {
    closeModal();
    throw err;
  }

  requestAnimationFrame(() => {
    progressBar?.classList.add("is-running");
    progressBar?.style.setProperty("--pay-sim-duration", `${durationMs}ms`);
  });

  const steps = [
    t("payment.simulation.connecting"),
    t("payment.simulation.awaiting"),
    t("payment.simulation.verifying"),
    t("payment.simulation.confirming"),
  ];
  let stepIndex = 0;
  const stepInterval = setInterval(() => {
    stepIndex = Math.min(stepIndex + 1, steps.length - 1);
    if (statusEl) statusEl.textContent = steps[stepIndex];
  }, durationMs / steps.length);

  await sleep(durationMs);
  clearInterval(stepInterval);

  let result;
  try {
    result = await onComplete();
  } catch (err) {
    closeModal();
    throw err;
  }

  if (onSuccess) onSuccess(result);

  showRedirectState(bodyEl, titleEl);

  await sleep(REDIRECT_DELAY_MS);
  closeModal();

  if (result.confirmation_url) {
    window.location.href = result.confirmation_url;
  }

  return result;
}

function buildModalElement(methodLabel, formattedAmount) {
  const modal = document.createElement("div");
  modal.className = "med-modal med-modal--sm pay-sim-modal";
  modal.innerHTML = `
    <div class="med-modal__header pay-sim__header">
      <div>
        <h2 class="med-modal__title" id="modal-title">${escapeHtml(t("payment.simulation.processing"))}</h2>
        <p class="med-modal__subtitle">${escapeHtml(methodLabel)} · ${escapeHtml(formattedAmount)}</p>
      </div>
      <button class="med-modal__close" aria-label="${escapeHtml(t("common.close"))}" style="display:none"><i class="bi bi-x-lg"></i></button>
    </div>
    <div class="med-modal__body pay-sim__body">
      <div class="pay-sim__processing">
        <div class="pay-sim__spinner-wrap">
          <span class="med-spinner med-spinner--lg pay-sim__spinner"></span>
        </div>
        <p class="pay-sim__status">${escapeHtml(t("payment.simulation.connecting"))}</p>
        <div class="pay-sim__progress">
          <div class="pay-sim__progress-bar"></div>
        </div>
        <p class="pay-sim__hint">${escapeHtml(t("payment.simulation.doNotClose"))}</p>
      </div>
    </div>
  `;
  return modal;
}

function showRedirectState(bodyEl, titleEl) {
  if (titleEl) titleEl.textContent = t("payment.simulation.successTitle");
  if (!bodyEl) return;

  bodyEl.classList.add("pay-sim__body--success");
  bodyEl.innerHTML = `
    <div class="pay-sim__success pay-sim__success--compact">
      <div class="pay-sim__checkmark pay-sim__checkmark--sm" aria-hidden="true">
        <svg viewBox="0 0 52 52" class="pay-sim__check-svg">
          <circle class="pay-sim__check-circle" cx="26" cy="26" r="24" fill="none"/>
          <path class="pay-sim__check-path" fill="none" d="M14 27l8 8 16-16"/>
        </svg>
      </div>
      <p class="pay-sim__redirect-only">${escapeHtml(t("payment.simulation.redirecting"))}</p>
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
