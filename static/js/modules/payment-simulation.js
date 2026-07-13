/**
 * Payment Simulation Module
 * Reuses med-modal for processing + success flow (simulation only).
 */

import { openModal, closeModal } from "../core/modal.js";
import { toast } from "../core/toast.js";
import { t } from "../i18n/translator.js";
import { paymentStatus } from "../i18n/statusLabels.js";

const DEFAULT_DURATION_MS = 6000;
const REDIRECT_DELAY_MS = 2200;

/**
 * @param {Object} options
 * @param {string} options.methodLabel
 * @param {number} options.amount
 * @param {string} options.currency
 * @param {number} [options.durationMs=6000]
 * @param {() => Promise<any>} options.onInitiate - called when modal opens
 * @param {() => Promise<any>} options.onComplete - called after animation
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

  showSuccessState(bodyEl, result, methodLabel, formattedAmount);
  toast.success(
    t("toast.paymentSuccessful"),
    `${t("payment.simulation.reference")}: ${result.reference_number}`
  );

  if (onSuccess) onSuccess(result);

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

function showSuccessState(bodyEl, result, methodLabel, formattedAmount) {
  if (!bodyEl) return;

  const statusLabel = paymentStatus(result.status, result.status_label);

  bodyEl.classList.add("pay-sim__body--success");
  bodyEl.innerHTML = `
    <div class="pay-sim__success">
      <div class="pay-sim__checkmark" aria-hidden="true">
        <svg viewBox="0 0 52 52" class="pay-sim__check-svg">
          <circle class="pay-sim__check-circle" cx="26" cy="26" r="24" fill="none"/>
          <path class="pay-sim__check-path" fill="none" d="M14 27l8 8 16-16"/>
        </svg>
      </div>
      <h3 class="pay-sim__success-title">${escapeHtml(t("payment.simulation.successTitle"))}</h3>
      <p class="pay-sim__success-message">${escapeHtml(t("payment.simulation.successMessage"))}</p>
      <div class="pay-sim__ref">
        <span>${escapeHtml(t("payment.simulation.reference"))}</span>
        <strong>${escapeHtml(result.reference_number)}</strong>
      </div>
      <dl class="pay-sim__details">
        <div><dt>${escapeHtml(t("payment.simulation.method"))}</dt><dd>${escapeHtml(methodLabel)}</dd></div>
        <div><dt>${escapeHtml(t("payment.simulation.amount"))}</dt><dd>${escapeHtml(formattedAmount)}</dd></div>
        <div><dt>${escapeHtml(t("payment.simulation.status"))}</dt><dd><span class="med-badge med-badge--success">${escapeHtml(statusLabel)}</span></dd></div>
      </dl>
      <p class="pay-sim__redirect">${escapeHtml(t("payment.simulation.redirecting"))}</p>
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
