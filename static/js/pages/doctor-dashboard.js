/**
 * Doctor Dashboard - practice management via Fetch API
 */

import { apiRequest } from "../utils/api.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { openModal, closeModal } from "../core/modal.js";
import { toast } from "../core/toast.js";
import { t, formatDate, timeAgo, translateGreeting } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";
import { appointmentStatus } from "../i18n/statusLabels.js";

const STATUS_CLASS = {
  pending: "pending",
  scheduled: "scheduled",
  confirmed: "confirmed",
  completed: "completed",
  cancelled: "cancelled",
  no_show: "cancelled",
};

let profileUrl = "#";
let currentMonth = new Date();
let statusFilter = "";
let searchTimer = null;
let dashboardData = null;
let calendarDays = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function revealStagger(container) {
  if (!container) return;
  container.querySelectorAll("[data-reveal-item]").forEach((el, i) => {
    el.style.animationDelay = `${i * 0.06}s`;
  });
  initScrollReveal();
}

function emptyState(icon, title, subtitle) {
  return `
    <div class="med-empty med-empty--compact">
      <div class="med-empty__illustration"><i class="bi bi-${icon}"></i></div>
      <p class="med-empty__title">${title}</p>
      <p class="med-empty__subtitle">${subtitle}</p>
    </div>`;
}

function apptCard(a, i = 0) {
  const cls = STATUS_CLASS[a.status] || "scheduled";
  const statusLabel = appointmentStatus(a.status, a.status_label);
  return `
    <article class="ddash-appt" data-appt-id="${a.id}" data-reveal-item style="animation-delay:${i * 0.05}s" role="button" tabindex="0">
      <div class="ddash-appt__avatar">${escapeHtml(a.patient_initials)}</div>
      <div class="ddash-appt__info">
        <div class="ddash-appt__name">${escapeHtml(a.patient_name)}</div>
        <div class="ddash-appt__meta">${escapeHtml(a.date_label)} · ${escapeHtml(a.time_range)}</div>
        ${a.patient_notes ? `<div class="ddash-appt__notes">${escapeHtml(a.patient_notes)}</div>` : ""}
      </div>
      <span class="med-status med-status--${cls}">${escapeHtml(statusLabel)}</span>
    </article>`;
}

function bindApptCards(container) {
  container?.querySelectorAll(".ddash-appt").forEach((el) => {
    const open = () => openAppointmentModal(Number(el.dataset.apptId));
    el.addEventListener("click", open);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        open();
      }
    });
  });
}

function renderOverview(data) {
  document.getElementById("ddash-greeting").textContent = translateGreeting(data.greeting);
  document.getElementById("ddash-doctor-name").textContent = data.doctor_name.replace(/^Dr\.\s*/, "");
  document.getElementById("ddash-specialty").textContent =
    `${data.specialization} · ${data.hospital}`;
  document.getElementById("ddash-profile-name").textContent =
    data.doctor_name.replace(/^Dr\.\s*/, "");

  profileUrl = data.profile_url;
  const profileLink = document.getElementById("ddash-profile-link");
  if (profileLink) profileLink.href = profileUrl;

  const s = data.stats;
  const items = [
    { icon: "sun", cls: "amber", value: s.today, label: t("dashboard.doctor.todayAppointments") },
    { icon: "calendar-event", cls: "teal", value: s.upcoming, label: t("dashboard.patient.upcoming") },
    { icon: "check-circle", cls: "green", value: s.completed, label: t("dashboard.patient.completed") },
    { icon: "x-circle", cls: "primary", value: s.cancelled, label: t("dashboard.doctor.tabs.cancelled") },
    { icon: "people", cls: "teal", value: s.total_patients, label: t("dashboard.doctor.patients") },
    { icon: "hourglass-split", cls: "amber", value: s.pending_approval, label: t("dashboard.doctor.tabs.pending") },
  ];

  const container = document.getElementById("ddash-stats");
  container.innerHTML = items.map((item, i) => `
    <div class="pdash-stat" data-reveal-item style="animation-delay:${i * 0.06}s">
      <div class="pdash-stat__icon pdash-stat__icon--${item.cls}"><i class="bi bi-${item.icon}"></i></div>
      <div class="pdash-stat__value">${item.value}</div>
      <div class="pdash-stat__label">${item.label}</div>
    </div>
  `).join("");
  revealStagger(container);

  const badge = document.getElementById("ddash-today-count");
  if (badge) {
    badge.hidden = s.today === 0;
    badge.textContent = `${s.today}`;
  }
}

function renderToday(list) {
  const container = document.getElementById("ddash-today");
  if (!list.length) {
    container.innerHTML = emptyState(
      "cup-hot",
      t("dashboard.doctor.noTodayTitle"),
      t("dashboard.doctor.noTodayMessage")
    );
    return;
  }
  container.innerHTML = list.map((a, i) => apptCard(a, i)).join("");
  bindApptCards(container);
  revealStagger(container);
}

function renderAppointments(list) {
  const container = document.getElementById("ddash-appointments");
  if (!list.length) {
    container.innerHTML = emptyState(
      "calendar-x",
      t("dashboard.doctor.noAppointmentsTitle"),
      t("dashboard.doctor.noAppointmentsMessage")
    );
    return;
  }
  container.innerHTML = list.map((a, i) => apptCard(a, i)).join("");
  bindApptCards(container);
  revealStagger(container);
}

function renderPatients(list) {
  const container = document.getElementById("ddash-patients");
  if (!list.length) {
    container.innerHTML = emptyState(
      "person",
      t("dashboard.doctor.noPatientsTitle"),
      t("dashboard.doctor.noPatientsMessage")
    );
    return;
  }
  container.innerHTML = list.map((p, i) => `
    <div class="ddash-patient" data-patient-id="${p.id}" data-reveal-item style="animation-delay:${i * 0.05}s" role="button" tabindex="0">
      <div class="ddash-appt__avatar">${escapeHtml(p.initials)}</div>
      <div class="ddash-appt__info">
        <div class="ddash-appt__name">${escapeHtml(p.name)}</div>
        <div class="ddash-appt__meta">${p.total_visits} visit${p.total_visits !== 1 ? "s" : ""}${p.last_visit ? ` · ${formatDate(p.last_visit)}` : ""}</div>
      </div>
      <i class="bi bi-chevron-right ddash-patient__arrow"></i>
    </div>
  `).join("");

  container.querySelectorAll(".ddash-patient").forEach((el) => {
    const open = () => openPatientModal(Number(el.dataset.patientId));
    el.addEventListener("click", open);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        open();
      }
    });
  });
  revealStagger(container);
}

function renderActivity(list) {
  const container = document.getElementById("ddash-activity");
  if (!list.length) {
    container.innerHTML = emptyState(
      "clock-history",
      t("dashboard.doctor.noActivityTitle"),
      t("dashboard.doctor.noActivityMessage")
    );
    return;
  }
  container.innerHTML = list.map((a, i) => {
    const statusLabel = appointmentStatus(a.status, a.status_label);
    return `
    <div class="ddash-activity-item" data-reveal-item style="animation-delay:${i * 0.04}s">
      <div class="ddash-activity-item__dot"></div>
      <div>
        <div class="ddash-activity-item__title">${escapeHtml(a.patient_name)} - ${escapeHtml(statusLabel)}</div>
        <div class="ddash-activity-item__meta">${escapeHtml(a.notes || "")} · ${timeAgo(a.created_at)}</div>
      </div>
    </div>
  `;
  }).join("");
  revealStagger(container);
}

function renderCalendar(days) {
  const container = document.getElementById("ddash-calendar");
  const label = document.getElementById("ddash-cal-label");
  const locale = document.documentElement.lang === "sw" ? "sw-TZ" : "en-GB";
  const monthStr = currentMonth.toLocaleDateString(locale, { month: "long", year: "numeric" });
  if (label) label.textContent = monthStr;

  const firstDow = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).getDay();
  const offset = (firstDow + 6) % 7;
  const headers = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(2024, 0, 1 + i);
    return d.toLocaleDateString(locale, { weekday: "narrow" });
  });

  let html = headers.map((h) => `<span class="ddash-cal__head">${h}</span>`).join("");
  for (let i = 0; i < offset; i++) html += `<span class="ddash-cal__day ddash-cal__day--empty"></span>`;

  const today = new Date().toISOString().slice(0, 10);
  days.forEach((d, i) => {
    const active = d.count > 0 ? " ddash-cal__day--active" : "";
    const isToday = d.date === today ? " ddash-cal__day--today" : "";
    html += `
      <button type="button" class="ddash-cal__day${active}${isToday}"
        data-date="${d.date}" data-reveal-item style="animation-delay:${(i % 7) * 0.02}s"
        title="${d.count}">
        <span>${d.label}</span>
        ${d.count ? `<em>${d.count}</em>` : ""}
      </button>`;
  });

  container.innerHTML = html;
  container.querySelectorAll(".ddash-cal__day[data-date]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("ddash-date-filter").value = btn.dataset.date;
      loadAppointments();
    });
  });
  revealStagger(container);
}

async function openAppointmentModal(id) {
  try {
    const a = await apiRequest(`/doctor/dashboard/appointments/${id}`);
    const cls = STATUS_CLASS[a.status] || "scheduled";
    const statusLabel = appointmentStatus(a.status, a.status_label);
    const canApprove = ["pending", "scheduled"].includes(a.status);
    const canComplete = ["confirmed", "scheduled"].includes(a.status);
    const canCancel = ["pending", "scheduled", "confirmed"].includes(a.status);

    const modal = document.createElement("div");
    modal.className = "med-modal med-modal--lg ddash-modal";
    modal.innerHTML = `
      <div class="med-modal__header">
        <div>
          <h2 class="med-modal__title" id="modal-title">${escapeHtml(t("dashboard.doctor.appointments"))}</h2>
          <p class="med-modal__subtitle">${escapeHtml(a.patient_name)} · ${escapeHtml(a.date_label)}</p>
        </div>
        <button class="med-modal__close" aria-label="${escapeHtml(t("common.close"))}"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="med-modal__body">
        <dl class="ddash-detail">
          <div><dt>${escapeHtml(t("common.patient"))}</dt><dd>${escapeHtml(a.patient_name)}</dd></div>
          <div><dt>${escapeHtml(t("auth.register.phone"))}</dt><dd>${escapeHtml(a.patient_phone || t("common.dash"))}</dd></div>
          <div><dt>${escapeHtml(t("auth.register.email"))}</dt><dd>${escapeHtml(a.patient_email)}</dd></div>
          <div><dt>${escapeHtml(t("booking.stepSummary.date"))}</dt><dd>${escapeHtml(a.date_label)}</dd></div>
          <div><dt>${escapeHtml(t("booking.stepSummary.time"))}</dt><dd>${escapeHtml(a.time_range)}</dd></div>
          <div><dt>${escapeHtml(t("booking.stepSummary.status"))}</dt><dd><span class="med-status med-status--${cls}">${escapeHtml(statusLabel)}</span></dd></div>
          <div><dt>${escapeHtml(t("payment.confirmation.paymentStatus"))}</dt><dd>${escapeHtml(a.payment_status || t("common.dash"))}</dd></div>
          ${a.patient_notes ? `<div><dt>${escapeHtml(t("payment.confirmation.reason"))}</dt><dd>${escapeHtml(a.patient_notes)}</dd></div>` : ""}
          ${a.cancellation_reason ? `<div><dt>${escapeHtml(t("dashboard.doctor.tabs.cancelled"))}</dt><dd>${escapeHtml(a.cancellation_reason)}</dd></div>` : ""}
        </dl>
      </div>
      <div class="med-modal__footer ddash-modal__footer">
        <button type="button" class="med-btn med-btn--outline-neutral" data-action="patient" data-id="${a.patient_id}">
          <i class="bi bi-person"></i> ${escapeHtml(t("dashboard.doctor.viewPatient"))}
        </button>
        <div class="ddash-modal__actions">
          ${canApprove ? `<button type="button" class="med-btn med-btn--accent" data-action="approve" data-id="${a.id}"><i class="bi bi-check-lg"></i> ${escapeHtml(t("dashboard.doctor.approve"))}</button>` : ""}
          ${canComplete ? `<button type="button" class="med-btn med-btn--primary" data-action="complete" data-id="${a.id}"><i class="bi bi-check-circle"></i> ${escapeHtml(t("dashboard.doctor.complete"))}</button>` : ""}
          ${canCancel ? `<button type="button" class="med-btn med-btn--danger" data-action="cancel" data-id="${a.id}"><i class="bi bi-x-circle"></i> ${escapeHtml(t("dashboard.doctor.cancel"))}</button>` : ""}
        </div>
      </div>`;

    const backdrop = openModal(modal);
    backdrop.querySelector("[data-action='patient']")?.addEventListener("click", () => {
      closeModal();
      openPatientModal(a.patient_id);
    });
    backdrop.querySelector("[data-action='approve']")?.addEventListener("click", () => actionAppointment("approve", a.id));
    backdrop.querySelector("[data-action='complete']")?.addEventListener("click", () => actionAppointment("complete", a.id));
    backdrop.querySelector("[data-action='cancel']")?.addEventListener("click", () => promptCancel(a.id));
  } catch (err) {
    toast.error(t("toast.error"), err.message || t("dashboard.doctor.loadError"));
  }
}

async function openPatientModal(id) {
  try {
    const p = await apiRequest(`/doctor/dashboard/patients/${id}`);
    const modal = document.createElement("div");
    modal.className = "med-modal med-modal--lg ddash-modal";
    modal.innerHTML = `
      <div class="med-modal__header">
        <div>
          <h2 class="med-modal__title" id="modal-title">${escapeHtml(t("common.patient"))}</h2>
          <p class="med-modal__subtitle">${escapeHtml(p.name)}</p>
        </div>
        <button class="med-modal__close" aria-label="${escapeHtml(t("common.close"))}"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="med-modal__body">
        <div class="ddash-patient-hero">
          <div class="ddash-appt__avatar ddash-appt__avatar--lg">${escapeHtml(p.initials)}</div>
          <div>
            <strong>${escapeHtml(p.name)}</strong>
            <p>${escapeHtml(p.email)}${p.phone ? ` · ${escapeHtml(p.phone)}` : ""}</p>
          </div>
        </div>
        <dl class="ddash-detail">
          <div><dt>${escapeHtml(t("dashboard.patient.totalVisits"))}</dt><dd>${p.total_visits}</dd></div>
          <div><dt>${escapeHtml(t("dashboard.patient.upcoming"))}</dt><dd>${p.upcoming_visits}</dd></div>
          <div><dt>${escapeHtml(t("dashboard.patient.completed"))}</dt><dd>${p.completed_visits}</dd></div>
          <div><dt>${escapeHtml(t("dashboard.doctor.recentActivity"))}</dt><dd>${p.last_visit ? formatDate(p.last_visit) : t("common.dash")}</dd></div>
        </dl>
        ${p.recent_notes.length ? `<div class="ddash-notes"><h4>${escapeHtml(t("dashboard.doctor.recentActivity"))}</h4><ul>${p.recent_notes.map((n) => `<li>${escapeHtml(n)}</li>`).join("")}</ul></div>` : ""}
      </div>`;
    openModal(modal);
  } catch (err) {
    toast.error(t("toast.error"), err.message || t("dashboard.doctor.loadError"));
  }
}

async function actionAppointment(action, id) {
  try {
    await apiRequest(`/doctor/dashboard/appointments/${id}/${action}`, { method: "PATCH" });
    closeModal();
    toast.success(t("toast.updated"), t("dashboard.admin.doctorUpdated"));
    await refreshAll();
  } catch (err) {
    toast.error(t("toast.actionFailed"), err.message || t("payment.toast.failed"));
  }
}

function promptCancel(id) {
  const reason = window.prompt(t("dashboard.doctor.cancelReasonPrompt"));
  if (!reason || reason.trim().length < 3) {
    toast.warning(t("toast.reasonRequired"), t("dashboard.doctor.cancelReasonRequired"));
    return;
  }
  apiRequest(`/doctor/dashboard/appointments/${id}/cancel`, {
    method: "PATCH",
    body: JSON.stringify({ reason: reason.trim() }),
  })
    .then(() => {
      closeModal();
      toast.success(t("toast.cancelled"), t("dashboard.doctor.cancelled"));
      return refreshAll();
    })
    .catch((err) => toast.error(t("toast.cancelFailed"), err.message));
}

async function loadAppointments() {
  const q = document.getElementById("ddash-search")?.value?.trim() || "";
  const date = document.getElementById("ddash-date-filter")?.value || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (date) params.set("date", date);
  if (statusFilter) params.set("status", statusFilter);
  const qs = params.toString();
  const list = await apiRequest(`/doctor/dashboard/appointments${qs ? `?${qs}` : ""}`);
  if (dashboardData) dashboardData.appointments = list;
  renderAppointments(list);
}

async function loadCalendar() {
  const month = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}`;
  const days = await apiRequest(`/doctor/dashboard/calendar?month=${month}`);
  calendarDays = days;
  renderCalendar(days);
}

function renderDashboardStatic() {
  document.querySelectorAll(".ddash-tab").forEach((tab) => {
    const status = tab.dataset.status;
    const key = status ? `dashboard.doctor.tabs.${status}` : "dashboard.doctor.tabs.all";
    const label = tab.querySelector(".ddash-tab__label");
    if (label) label.textContent = t(key);
  });
}

async function refreshAll() {
  const [overview, today, patients, activity] = await Promise.all([
    apiRequest("/doctor/dashboard/overview"),
    apiRequest("/doctor/dashboard/appointments/today"),
    apiRequest("/doctor/dashboard/patients"),
    apiRequest("/doctor/dashboard/activity"),
  ]);
  dashboardData = { overview, today, patients, activity };
  renderOverview(overview);
  renderToday(today);
  renderPatients(patients);
  renderActivity(activity);
  await loadAppointments();
  await loadCalendar();
}

function bindFilters() {
  document.getElementById("ddash-search")?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadAppointments, 300);
  });
  document.getElementById("ddash-date-filter")?.addEventListener("change", loadAppointments);

  document.querySelectorAll(".ddash-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".ddash-tab").forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");
      statusFilter = tab.dataset.status || "";
      loadAppointments();
    });
  });

  document.getElementById("ddash-cal-prev")?.addEventListener("click", () => {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
    loadCalendar();
  });
  document.getElementById("ddash-cal-next")?.addEventListener("click", () => {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
    loadCalendar();
  });
}

function onLangChange() {
  renderDashboardStatic();
  if (dashboardData) {
    renderOverview(dashboardData.overview);
    renderToday(dashboardData.today);
    renderPatients(dashboardData.patients);
    renderActivity(dashboardData.activity);
    if (dashboardData.appointments) renderAppointments(dashboardData.appointments);
  }
  if (calendarDays) renderCalendar(calendarDays);
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();
  renderDashboardStatic();
  bindFilters();
  refreshAll().catch(() => toast.error(t("toast.dashboardError"), t("dashboard.doctor.loadError")));
  onLanguageChange(onLangChange);
});
