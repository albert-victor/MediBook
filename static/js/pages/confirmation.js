/**
 * Appointment confirmation page
 */

import { apiRequest } from "../utils/api.js";
import { setVisible } from "../utils/visibility.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { formatDate, formatTime } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";
import { appointmentStatus, paymentStatus } from "../i18n/statusLabels.js";

let confirmationData = null;

function formatMoney(amount, currency) {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function formatPaidAt(iso) {
  const d = new Date(iso);
  return `${formatDate(d, { weekday: "short" })} ${formatTime(d)}`;
}

function renderConfirmation(data) {
  document.getElementById("conf-doctor").textContent = data.doctor_name;
  document.getElementById("conf-department").textContent = data.department;
  document.getElementById("conf-hospital").textContent = data.hospital;
  document.getElementById("conf-date").textContent = data.date_label;
  document.getElementById("conf-time").textContent = data.time_range;
  document.getElementById("conf-status").textContent = appointmentStatus(data.status, data.status_label);

  const notesRow = document.getElementById("conf-notes-row");
  if (data.patient_notes) {
    setVisible(notesRow, true);
    document.getElementById("conf-notes").textContent = data.patient_notes;
  } else {
    setVisible(notesRow, false);
  }

  document.getElementById("conf-reference").textContent = data.reference_number;
  document.getElementById("conf-method").textContent = data.payment_method_label;
  document.getElementById("conf-amount").textContent = formatMoney(data.consultation_fee, data.currency);
  document.getElementById("conf-paid-at").textContent = formatPaidAt(data.paid_at);
  document.getElementById("conf-receipt-doctor").textContent = data.doctor_name;
  document.getElementById("conf-payment-status").textContent = paymentStatus(
    data.payment_status,
    data.payment_status_label
  );
}

async function loadConfirmation() {
  const id = document.getElementById("confirmation-page")?.dataset.appointmentId;
  if (!id) return;

  try {
    confirmationData = await apiRequest(`/payments/appointment/${id}/confirmation`);
    setVisible(document.getElementById("confirmation-loading"), false);
    setVisible(document.getElementById("confirmation-content"), true);
    renderConfirmation(confirmationData);
    initScrollReveal();
  } catch {
    setVisible(document.getElementById("confirmation-loading"), false);
    setVisible(document.getElementById("confirmation-error"), true);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();
  document.getElementById("btn-print-receipt")?.addEventListener("click", () => window.print());
  loadConfirmation();
  onLanguageChange(() => {
    if (confirmationData) renderConfirmation(confirmationData);
  });
});
