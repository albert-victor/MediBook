/**
 * Appointment Booking Engine - multi-step wizard (Fetch API, no reloads)
 */

import { apiRequest } from "../utils/api.js";
import { setVisible } from "../utils/visibility.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { toast } from "../core/toast.js";
import { t, formatDate } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";

const state = {
  step: 1,
  doctors: [],
  doctor: null,
  date: "",
  slots: [],
  slot: null,
  reason: "",
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatFee(amount, currency) {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function formatDateLabel(isoDate) {
  return formatDate(`${isoDate}T12:00:00`, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function getPreselectedDoctorId() {
  return new URLSearchParams(window.location.search).get("doctor");
}

function showAlert(message, title = null) {
  const alert = document.getElementById("booking-alert");
  const titleEl = document.getElementById("booking-alert-title");
  const msgEl = document.getElementById("booking-alert-message");
  if (!alert) return;
  titleEl.textContent = title ?? t("booking.alertTitle");
  msgEl.textContent = message;
  setVisible(alert, true);
  alert.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideAlert() {
  setVisible(document.getElementById("booking-alert"), false);
}

function updateStepLabels() {
  const stepKeys = ["doctor", "date", "time", "reason", "summary"];
  document.querySelectorAll(".booking-steps__item").forEach((el) => {
    const n = Number(el.dataset.step);
    const label = el.querySelector(".booking-steps__label");
    if (label && stepKeys[n - 1]) {
      label.textContent = t(`booking.steps.${stepKeys[n - 1]}`);
    }
  });
}

function setStep(step) {
  state.step = step;

  document.querySelectorAll(".booking-steps__item").forEach((el) => {
    const n = Number(el.dataset.step);
    el.classList.toggle("is-active", n === step);
    el.classList.toggle("is-complete", n < step);
  });

  document.querySelectorAll("[data-step-panel]").forEach((panel) => {
    const n = Number(panel.dataset.stepPanel);
    const active = n === step;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });

  updateStepLabels();

  const btnBack = document.getElementById("btn-back");
  const btnNext = document.getElementById("btn-next");
  if (btnBack) btnBack.hidden = step === 1;

  if (btnNext) {
    updateNextButton();
  }

  initScrollReveal();
}

function canProceed() {
  switch (state.step) {
    case 1:
      return !!state.doctor;
    case 2:
      return !!state.date;
    case 3:
      return !!state.slot;
    case 4:
      return true;
    case 5:
      return !!state.doctor && !!state.slot;
    default:
      return false;
  }
}

function getCtaSummary() {
  switch (state.step) {
    case 1:
      if (!state.doctor) return { label: "", value: "" };
      return {
        label: t("booking.cta.selectedDoctor"),
        value: `${state.doctor.name} · ${state.doctor.specialization}`,
      };
    case 2:
      if (!state.date) return { label: "", value: "" };
      return {
        label: t("booking.cta.selectedDate"),
        value: formatDateLabel(state.date),
      };
    case 3:
      if (!state.slot) return { label: "", value: "" };
      return {
        label: t("booking.cta.selectedTime"),
        value: `${state.slot.start_time} – ${state.slot.end_time}`,
      };
    case 4:
      return {
        label: t("booking.cta.almostDone"),
        value: state.doctor?.name ?? "",
      };
    case 5:
      return {
        label: t("booking.cta.reviewBooking"),
        value:
          state.doctor && state.slot
            ? `${formatDateLabel(state.date)} · ${state.slot.start_time}`
            : "",
      };
    default:
      return { label: "", value: "" };
  }
}

function revealBookingCta() {
  const cta = document.getElementById("booking-cta");
  if (!cta) return;
  requestAnimationFrame(() => {
    cta.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
}

function updateNextButton() {
  const cta = document.getElementById("booking-cta");
  const btn = document.getElementById("btn-next");
  const btnBack = document.getElementById("btn-back");
  const can = canProceed();
  const showCta = state.step >= 4 || can;

  if (cta) {
    cta.classList.toggle("is-visible", showCta);
    cta.setAttribute("aria-hidden", showCta ? "false" : "true");
    cta.classList.toggle("is-ready", showCta && can);
  }
  if (btn) btn.disabled = !can;
  if (btnBack) btnBack.hidden = state.step === 1;

  const labelEl = document.getElementById("booking-cta-label");
  const valueEl = document.getElementById("booking-cta-value");
  const summary = getCtaSummary();
  if (labelEl) labelEl.textContent = summary.label;
  if (valueEl) valueEl.textContent = summary.value;

  if (btn && showCta && can && state.step === 1 && state.doctor) {
    const name = state.doctor.name.replace(/^Dr\.\s*/i, "");
    btn.innerHTML = `${t("booking.cta.continueWith", { name })} <i class="bi bi-arrow-right"></i>`;
  } else if (btn && state.step === 5) {
    btn.innerHTML = `<i class="bi bi-credit-card"></i> ${t("booking.proceedPayment")}`;
  } else if (btn) {
    btn.innerHTML = `${t("common.continue")} <i class="bi bi-arrow-right"></i>`;
  }
}

function renderDoctors() {
  const container = document.getElementById("booking-doctors");
  if (!container) return;

  container.hidden = false;
  container.style.display = "";

  if (!state.doctors.length) {
    container.innerHTML = `<p class="med-caption">${t("dashboard.patient.noDoctorsAvailable")}</p>`;
    return;
  }

  container.innerHTML = state.doctors
    .map(
      (d, i) => `
    <button type="button"
      class="booking-doctor${state.doctor?.id === d.id ? " is-selected" : ""}"
      data-doctor-id="${d.id}"
      data-reveal-item
      style="transition-delay:${i * 50}ms">
      <div class="booking-doctor__visual">
        ${
          d.image_url
            ? `<img class="booking-doctor__photo" src="${escapeHtml(d.image_url)}" alt="" loading="lazy">`
            : `<div class="booking-doctor__avatar booking-doctor__avatar--${d.avatar_gradient}">${escapeHtml(d.initials)}</div>`
        }
      </div>
      <div class="booking-doctor__info">
        <h3>${escapeHtml(d.name)}</h3>
        <p>${escapeHtml(d.specialization)} · ${escapeHtml(d.hospital)}</p>
      </div>
      <span class="booking-doctor__fee">${formatFee(d.fee, d.currency)}</span>
    </button>
  `
    )
    .join("");

  container.querySelectorAll(".booking-doctor").forEach((btn) => {
    btn.addEventListener("click", () => selectDoctor(Number(btn.dataset.doctorId)));
  });

  initScrollReveal();
}

function selectDoctor(id) {
  const isNewSelection = state.doctor?.id !== id;
  state.doctor = state.doctors.find((d) => d.id === id) || null;
  state.date = "";
  state.slots = [];
  state.slot = null;

  document.querySelectorAll(".booking-doctor").forEach((el) => {
    el.classList.toggle("is-selected", Number(el.dataset.doctorId) === id);
  });

  const nameEl = document.getElementById("selected-doctor-name");
  if (nameEl && state.doctor) nameEl.textContent = state.doctor.name;

  updateNextButton();
  if (state.step === 1 && state.doctor && isNewSelection) {
    revealBookingCta();
  }
}

function setDoctorsLoading(isLoading) {
  const loading = document.getElementById("doctors-loading");
  const container = document.getElementById("booking-doctors");
  setVisible(loading, isLoading);
  if (container && isLoading) setVisible(container, false);
}

async function loadDoctors() {
  hideAlert();
  setDoctorsLoading(true);
  try {
    state.doctors = await apiRequest("/appointments/doctors");
    if (!Array.isArray(state.doctors)) {
      throw new Error(t("booking.loadDoctorsFailed"));
    }
    renderDoctors();

    const preselect = getPreselectedDoctorId();
    if (preselect) {
      const id = Number(preselect);
      if (state.doctors.some((d) => d.id === id)) {
        selectDoctor(id);
      }
    }
    hideAlert();
  } catch (err) {
    const msg = err.message || t("booking.loadDoctorsFailed");
    const patientsOnly = t("api.patientsOnly");
    const title =
      msg === patientsOnly || msg.includes(patientsOnly)
        ? t("booking.patientsOnlyTitle")
        : null;
    showAlert(msg, title);
  } finally {
    setDoctorsLoading(false);
  }
}

function renderSlots() {
  const container = document.getElementById("booking-slots");
  const empty = document.getElementById("slots-empty");
  const dateLabel = document.getElementById("selected-date-label");

  if (dateLabel && state.date) dateLabel.textContent = formatDateLabel(state.date);
  if (empty) empty.hidden = true;

  if (!state.slots.length) {
    if (empty) empty.hidden = false;
    if (container) container.innerHTML = "";
    return;
  }

  if (!container) return;

  container.innerHTML = state.slots
    .map((s, i) => {
      const cls = s.is_available ? "booking-slot--available" : "booking-slot--booked";
      const attrs = s.is_available
        ? `data-slot-id="${s.id}" tabindex="0" role="button"`
        : `disabled aria-disabled="true"`;
      return `
      <button type="button" class="booking-slot ${cls}" ${attrs}
        data-reveal-item style="transition-delay:${i * 40}ms">
        <span class="booking-slot__time">${s.start_time}</span>
        <span class="booking-slot__end">${s.end_time}</span>
      </button>
    `;
    })
    .join("");

  container.querySelectorAll(".booking-slot--available").forEach((btn) => {
    const pick = () => selectSlot(Number(btn.dataset.slotId));
    btn.addEventListener("click", pick);
    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pick();
      }
    });
  });

  if (state.slot) {
    document.querySelectorAll(".booking-slot--available").forEach((el) => {
      el.classList.toggle("is-selected", Number(el.dataset.slotId) === state.slot.id);
    });
  }

  initScrollReveal();
}

async function loadSlots() {
  if (!state.doctor || !state.date) return;

  const loading = document.getElementById("slots-loading");
  const container = document.getElementById("booking-slots");
  const empty = document.getElementById("slots-empty");
  const dateLabel = document.getElementById("selected-date-label");

  if (dateLabel) dateLabel.textContent = formatDateLabel(state.date);
  if (loading) loading.hidden = false;
  if (container) container.innerHTML = "";
  if (empty) empty.hidden = true;
  hideAlert();

  state.slots = [];
  state.slot = null;
  updateNextButton();

  try {
    state.slots = await apiRequest(
      `/appointments/slots?doctor_id=${state.doctor.id}&date=${state.date}`
    );
  } catch (err) {
    showAlert(err.message || t("booking.loadSlotsFailed"));
    if (loading) loading.hidden = true;
    return;
  }

  if (loading) loading.hidden = true;
  renderSlots();
}

function selectSlot(id) {
  state.slot = state.slots.find((s) => s.id === id) || null;

  document.querySelectorAll(".booking-slot--available").forEach((el) => {
    el.classList.toggle("is-selected", Number(el.dataset.slotId) === id);
  });

  updateNextButton();
  if (state.step === 3 && state.slot) {
    revealBookingCta();
  }
}

function fillSummary() {
  if (!state.doctor || !state.slot) return;

  document.getElementById("summary-doctor").textContent = state.doctor.name;
  document.getElementById("summary-department").textContent = state.doctor.department;
  document.getElementById("summary-date").textContent = formatDateLabel(state.date);
  document.getElementById("summary-time").textContent = `${state.slot.start_time} - ${state.slot.end_time}`;
  document.getElementById("summary-fee").textContent = formatFee(state.doctor.fee, state.doctor.currency);
}

async function submitBooking() {
  const btn = document.getElementById("btn-next");
  if (!state.doctor || !state.slot) return;

  btn.classList.add("med-btn--loading");
  btn.disabled = true;
  hideAlert();

  try {
    const result = await apiRequest("/appointments", {
      method: "POST",
      body: JSON.stringify({
        doctor_id: state.doctor.id,
        availability_id: state.slot.id,
        patient_notes: state.reason.trim() || null,
      }),
    });

    toast.success(t("toast.appointmentBooked"), t("booking.redirectPayment"));
    window.location.href = result.payment_url;
  } catch (err) {
    const msg = err.message || t("booking.bookingFailed");
    const slotTaken = t("api.slotTaken");

    if (err.message?.includes("already been booked") || msg === slotTaken || msg.includes(slotTaken)) {
      showAlert(t("booking.slotConflict"), t("booking.slotUnavailableTitle"));
      setStep(3);
      await loadSlots();
    } else {
      showAlert(msg);
      toast.error(t("toast.bookingFailed"), msg);
    }

    btn.classList.remove("med-btn--loading");
    updateNextButton();
  }
}

function goNext() {
  if (!canProceed()) return;

  if (state.step === 2 && state.date) {
    setStep(3);
    loadSlots();
    return;
  }

  if (state.step === 4) {
    state.reason = document.getElementById("booking-reason")?.value || "";
    fillSummary();
  }

  if (state.step === 5) {
    submitBooking();
    return;
  }

  setStep(state.step + 1);
}

function goBack() {
  if (state.step <= 1) return;
  hideAlert();
  setStep(state.step - 1);
}

function refreshCurrentStep() {
  setStep(state.step);
  if (state.step === 1 && state.doctors.length) renderDoctors();
  if (state.step === 3 && state.date) renderSlots();
  if (state.step === 5) fillSummary();
}

function bindEvents() {
  document.getElementById("btn-next")?.addEventListener("click", goNext);
  document.getElementById("btn-back")?.addEventListener("click", goBack);
  document.getElementById("booking-alert-close")?.addEventListener("click", hideAlert);

  const dateInput = document.getElementById("booking-date");
  if (dateInput) {
    dateInput.min = todayIso();
    dateInput.max = new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    dateInput.addEventListener("change", () => {
      state.date = dateInput.value;
      state.slot = null;
      updateNextButton();
      if (state.step === 2 && state.date) {
        revealBookingCta();
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();
  bindEvents();
  setStep(1);
  loadDoctors();
  onLanguageChange(refreshCurrentStep);
});

window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    hideAlert();
    loadDoctors();
  }
});
