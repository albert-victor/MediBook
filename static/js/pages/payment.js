/**
 * Payment page - integrates Payment Simulation module
 */

import { apiRequest } from "../utils/api.js";
import { setVisible } from "../utils/visibility.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { toast } from "../core/toast.js";
import { runPaymentSimulation } from "../modules/payment-simulation.js";
import { t } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";
import { paymentMethod } from "../i18n/statusLabels.js";

let context = null;
let selectedMethod = "mpesa";
let selectedMethodLabel = "M-Pesa";

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatMoney(amount, currency) {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function getAppointmentId() {
  const raw = document.getElementById("payment-page")?.dataset.appointmentId?.trim();
  if (!raw) return null;
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}

function getMethodLabel(methodId) {
  const fromApi = context?.methods?.find((m) => m.id === methodId)?.label;
  return paymentMethod(methodId, fromApi || methodId);
}

function showPaymentError(message, title = null) {
  const loading = document.getElementById("payment-loading");
  const content = document.getElementById("payment-content");
  const error = document.getElementById("payment-error");
  const messageEl = document.getElementById("payment-error-message");
  const titleEl = error?.querySelector(".med-empty__title");

  setVisible(loading, false);
  setVisible(content, false);
  setVisible(error, true);
  if (messageEl) messageEl.textContent = message || t("payment.notFound");
  if (titleEl) titleEl.textContent = title || t("payment.unavailableTitle");
}

function renderMethods(methods = []) {
  const container = document.getElementById("payment-methods");
  if (!container) return;

  if (!methods.length) {
    container.innerHTML = `
      <p class="med-caption">${t("payment.noMethods")}</p>
    `;
    return;
  }

  container.innerHTML = methods
    .map(
      (m, i) => {
        const label = paymentMethod(m.id, m.label);
        return `
    <button type="button"
      class="payment-method${m.id === selectedMethod ? " is-selected" : ""}"
      data-method="${m.id}"
      data-label="${escapeHtml(label)}"
      data-reveal-item
      style="transition-delay:${i * 50}ms">
      <i class="bi ${m.icon}"></i>
      <span>${escapeHtml(label)}</span>
    </button>
  `;
      }
    )
    .join("");

  container.querySelectorAll(".payment-method").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedMethod = btn.dataset.method;
      selectedMethodLabel = btn.dataset.label;
      container.querySelectorAll(".payment-method").forEach((el) => {
        el.classList.toggle("is-selected", el.dataset.method === selectedMethod);
      });
    });
  });

  initScrollReveal();
}

function renderContext(ctx) {
  const doctorEl = document.getElementById("pay-doctor");
  const departmentEl = document.getElementById("pay-department");
  const datetimeEl = document.getElementById("pay-datetime");
  const amountEl = document.getElementById("pay-amount");

  if (!doctorEl || !departmentEl || !datetimeEl || !amountEl) {
    throw new Error("Payment form is missing required fields.");
  }

  doctorEl.textContent = ctx.doctor_name;
  departmentEl.textContent = ctx.department;
  datetimeEl.textContent = `${ctx.date_label} · ${ctx.time_range}`;
  amountEl.textContent = formatMoney(ctx.amount, ctx.currency);

  renderMethods(ctx.methods || []);

  if (ctx.payment_status === "completed") {
    showAlreadyPaid(ctx, { silent: true });
  } else {
    setVisible(document.getElementById("payment-form-section"), true);
    setVisible(document.getElementById("payment-already-paid"), false);
  }
}

function showAlreadyPaid(ctx, options = {}) {
  setVisible(document.getElementById("payment-form-section"), false);
  const notice = document.getElementById("payment-already-paid");
  setVisible(notice, true);
  if (notice) {
    const link = document.getElementById("btn-view-confirmation");
    if (link) link.href = `/appointments/confirmation/${getAppointmentId()}`;
  }
  if (!options.silent) {
    toast.info(t("toast.alreadyPaid"), t("payment.toast.alreadyPaid"));
  }
}

async function loadPayment() {
  const id = getAppointmentId();
  if (!id) {
    showPaymentError(t("payment.invalidAppointment"), t("payment.unavailableTitle"));
    return;
  }

  try {
    context = await apiRequest(`/payments/appointment/${id}`);
    setVisible(document.getElementById("payment-loading"), false);
    setVisible(document.getElementById("payment-content"), true);
    renderContext(context);
    initScrollReveal();
  } catch (err) {
    const msg = err.message || t("payment.notFound");
    const patientsOnly = t("api.patientsOnly");
    const title =
      msg === patientsOnly || msg.includes(patientsOnly)
        ? t("booking.patientsOnlyTitle")
        : t("payment.unavailableTitle");
    showPaymentError(msg, title);
  }
}

async function processPayment() {
  const phone = document.getElementById("payment-phone")?.value?.trim();
  if (!phone) {
    toast.warning(t("toast.phoneRequired"), t("payment.toast.phoneRequired"));
    return;
  }

  const btn = document.getElementById("btn-pay");
  btn.classList.add("med-btn--loading");
  btn.disabled = true;

  const appointmentId = getAppointmentId();
  if (!appointmentId || !context) {
    btn.classList.remove("med-btn--loading");
    btn.disabled = false;
    showPaymentError(t("payment.invalidAppointment"));
    return;
  }

  const payload = { payment_method: selectedMethod, phone_number: phone };

  try {
    await runPaymentSimulation({
      methodLabel: selectedMethodLabel || getMethodLabel(selectedMethod),
      amount: context.amount,
      currency: context.currency,
      durationMs: 6000,
      onInitiate: () =>
        apiRequest(`/payments/appointment/${appointmentId}/initiate`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),
      onComplete: () => apiRequest(`/payments/appointment/${appointmentId}/complete`, { method: "POST" }),
    });
  } catch (err) {
    btn.classList.remove("med-btn--loading");
    btn.disabled = false;
    toast.error(t("toast.paymentFailed"), err.message || t("payment.toast.failed"));
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();
  document.getElementById("btn-pay")?.addEventListener("click", processPayment);
  loadPayment();
  onLanguageChange(() => {
    if (context) renderContext(context);
  });
});
