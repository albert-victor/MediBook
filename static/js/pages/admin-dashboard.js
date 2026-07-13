/**
 * Admin Dashboard - platform management via Fetch API
 */

import { apiRequest } from "../utils/api.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { openModal, closeModal } from "../core/modal.js";
import { toast } from "../core/toast.js";
import { t, formatDate, translateGreeting } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";
import { appointmentStatus, paymentStatus, doctorActiveLabel } from "../i18n/statusLabels.js";
import {
  renderPieChart,
  renderVerticalBarChart,
  distributionToPieItems,
} from "../utils/admin-charts.js";

let specializations = [];
let overviewData = null;
let panelData = {};
let activePanel = "overview";

const PANEL_TITLE_KEYS = {
  overview: "dashboard.admin.nav.overview",
  doctors: "dashboard.admin.nav.doctors",
  patients: "dashboard.admin.nav.patients",
  appointments: "dashboard.admin.nav.appointments",
  payments: "dashboard.admin.nav.payments",
  reports: "dashboard.admin.nav.reports",
  notifications: "dashboard.admin.nav.notifications",
  settings: "dashboard.admin.nav.settings",
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatMoney(amount, currency = "TZS") {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function revealStagger(container) {
  if (!container) return;
  container.querySelectorAll("[data-reveal-item]").forEach((el, i) => {
    el.style.animationDelay = `${i * 0.05}s`;
  });
  initScrollReveal();
}

function tableEmptyRow(colspan, message) {
  return `<tr><td colspan="${colspan}" class="med-table__empty">${escapeHtml(message)}</td></tr>`;
}

function updatePageTitle(panelId) {
  const el = document.getElementById("adash-page-title");
  const key = PANEL_TITLE_KEYS[panelId];
  if (!el || !key) return;
  el.setAttribute("data-i18n", key);
  el.textContent = t(key);
}

function closeSidebar() {
  document.getElementById("adash-sidebar")?.classList.remove("is-open");
  document.getElementById("adash-sidebar-backdrop")?.classList.remove("is-visible");
}

function initSidebar() {
  const sidebar = document.getElementById("adash-sidebar");
  const backdrop = document.getElementById("adash-sidebar-backdrop");
  const toggle = document.getElementById("adash-sidebar-toggle");

  toggle?.addEventListener("click", () => {
    const open = sidebar?.classList.toggle("is-open");
    backdrop?.classList.toggle("is-visible", Boolean(open));
  });
  backdrop?.addEventListener("click", closeSidebar);
}

function emptyState(icon, title, subtitle) {
  return `<div class="med-empty med-empty--compact">
    <div class="med-empty__illustration"><i class="bi bi-${icon}"></i></div>
    <p class="med-empty__title">${title}</p>
    <p class="med-empty__subtitle">${subtitle}</p>
  </div>`;
}

function renderBarChart(container, items, { horizontal = false, color = "primary" } = {}) {
  if (!container || !items.length) {
    container.innerHTML = emptyState("bar-chart", t("dashboard.admin.noData"), t("dashboard.admin.noDataMessage"));
    return;
  }
  const max = Math.max(...items.map((i) => i.value), 1);
  container.innerHTML = items.map((item, i) => {
    const pct = Math.round((item.value / max) * 100);
    return `
      <div class="adash-bar${horizontal ? " adash-bar--h" : ""}" data-reveal-item style="animation-delay:${i * 0.04}s">
        <span class="adash-bar__label">${escapeHtml(item.label)}</span>
        <div class="adash-bar__track">
          <div class="adash-bar__fill adash-bar__fill--${color}" style="--bar-pct:${pct}%"></div>
        </div>
        <span class="adash-bar__value">${escapeHtml(item.display)}</span>
      </div>`;
  }).join("");
  revealStagger(container);
}

function switchPanel(panelId) {
  activePanel = panelId;
  document.querySelectorAll(".adash-panel").forEach((p) => {
    p.hidden = p.dataset.panel !== panelId;
    p.classList.toggle("is-active", p.dataset.panel === panelId);
  });
  document.querySelectorAll(".adash-nav__btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.panel === panelId);
  });
  updatePageTitle(panelId);
  closeSidebar();

  const loaders = {
    doctors: loadDoctors,
    patients: loadPatients,
    appointments: loadAppointments,
    payments: loadPayments,
    reports: loadReports,
    notifications: loadNotifications,
    settings: loadSettings,
  };
  loaders[panelId]?.();
}

function renderOverview(data) {
  overviewData = data;
  document.getElementById("adash-greeting").textContent = translateGreeting(data.greeting);
  document.getElementById("adash-subtitle").textContent =
    `${data.job_title} · ${data.department}`;
  document.getElementById("adash-profile-name").textContent = data.admin_name.split(" ")[0];

  const s = data.stats;
  const items = [
    { icon: "person-badge", cls: "primary", value: s.total_doctors, label: t("dashboard.admin.totalDoctors"), sub: t("dashboard.admin.activeCount", { count: s.active_doctors }) },
    { icon: "people", cls: "teal", value: s.total_patients, label: t("dashboard.admin.registeredPatients"), sub: t("dashboard.admin.activeCount", { count: s.active_patients }) },
    { icon: "calendar-day", cls: "amber", value: s.today_appointments, label: t("dashboard.admin.todayAppointments"), sub: t("dashboard.admin.totalCount", { count: s.total_appointments }) },
    { icon: "cash-stack", cls: "green", value: formatMoney(s.monthly_revenue, s.currency), label: t("dashboard.admin.monthlyRevenue"), sub: t("dashboard.admin.pendingCount", { count: s.pending_payments }) },
  ];

  document.getElementById("adash-stats").innerHTML = items.map((item) => `
    <div class="adash-stat">
      <div class="adash-stat__icon adash-stat__icon--${item.cls}"><i class="bi bi-${item.icon}"></i></div>
      <div class="adash-stat__value">${item.value}</div>
      <div class="adash-stat__label">${item.label}</div>
      <div class="adash-stat__sub">${item.sub}</div>
    </div>
  `).join("");

  renderBarChart(document.getElementById("chart-appointments"), data.charts.appointments_per_month, { color: "primary" });
  renderBarChart(document.getElementById("chart-payments"), data.charts.payments_per_month, { color: "green" });
  renderBarChart(document.getElementById("chart-doctors"), data.charts.doctor_distribution, { horizontal: true, color: "teal" });
}

function doctorStatus(d) {
  const statusCls = d.is_active ? (d.is_verified ? "confirmed" : "pending") : "cancelled";
  const statusLabel = d.is_active
    ? (d.is_verified ? doctorActiveLabel(true) : t("status.doctor.unverified", {}, "Unverified"))
    : doctorActiveLabel(false);
  return { statusCls, statusLabel };
}

function doctorRow(d) {
  const { statusCls, statusLabel } = doctorStatus(d);
  const deactivateLabel = t("toast.deactivated", {}, "Deactivate");
  return `
    <tr>
      <td class="med-table__cell--primary" data-label="${escapeHtml(t("common.doctor"))}">
        <strong>${escapeHtml(d.name)}</strong>
        <div class="adash-mono">${escapeHtml(d.license_number)}</div>
      </td>
      <td data-label="${escapeHtml(t("doctors.directory.filterSpecialty"))}">${escapeHtml(d.specialization)}</td>
      <td data-label="${escapeHtml(t("payment.confirmation.hospital"))}">${escapeHtml(d.hospital)}</td>
      <td data-label="${escapeHtml(t("doctors.profile.consultationFee"))}">${formatMoney(d.consultation_fee, d.currency)}</td>
      <td data-label="${escapeHtml(t("common.status"))}"><span class="med-status med-status--${statusCls}">${statusLabel}</span></td>
      <td class="med-table__cell--actions" data-label="${escapeHtml(t("common.actions"))}">
        <div class="adash-table-actions">
          <button type="button" class="med-btn med-btn--outline-neutral med-btn--sm" data-action="edit-doctor" data-id="${d.id}" title="${escapeHtml(t("common.edit"))}"><i class="bi bi-pencil"></i></button>
          ${d.is_active ? `<button type="button" class="med-btn med-btn--warning med-btn--sm" data-action="deactivate-doctor" data-id="${d.id}" title="${escapeHtml(deactivateLabel)}"><i class="bi bi-pause-circle"></i></button>` : ""}
          <button type="button" class="med-btn med-btn--danger med-btn--sm" data-action="delete-doctor" data-id="${d.id}" title="${escapeHtml(t("common.delete"))}"><i class="bi bi-trash"></i></button>
        </div>
      </td>
    </tr>`;
}

async function loadDoctors() {
  const container = document.getElementById("adash-doctors");
  try {
    const doctors = await apiRequest("/admin/dashboard/doctors");
    panelData.doctors = doctors;
    container.innerHTML = doctors.length
      ? doctors.map(doctorRow).join("")
      : tableEmptyRow(6, t("dashboard.admin.noDoctorsMessage"));
    bindDoctorActions(container);
  } catch {
    container.innerHTML = tableEmptyRow(6, t("dashboard.admin.loadError"));
  }
}

function bindDoctorActions(container) {
  container.querySelectorAll("[data-action='edit-doctor']").forEach((btn) => {
    btn.addEventListener("click", () => openEditDoctorModal(Number(btn.dataset.id)));
  });
  container.querySelectorAll("[data-action='deactivate-doctor']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm(t("dashboard.admin.deactivateDoctor"))) return;
      try {
        await apiRequest(`/admin/dashboard/doctors/${btn.dataset.id}/deactivate`, { method: "PATCH" });
        toast.success(t("toast.deactivated"), t("dashboard.admin.doctorDeactivated"));
        loadDoctors();
      } catch (err) {
        toast.error(t("toast.error"), err.message);
      }
    });
  });
  container.querySelectorAll("[data-action='delete-doctor']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm(t("dashboard.admin.deleteDoctor"))) return;
      try {
        await apiRequest(`/admin/dashboard/doctors/${btn.dataset.id}`, { method: "DELETE" });
        toast.success(t("toast.deleted"), t("dashboard.admin.doctorDeleted"));
        loadDoctors();
      } catch (err) {
        toast.error(t("toast.cannotDelete"), err.message);
      }
    });
  });
}

function specOptions(selectedId) {
  return specializations.map((s) =>
    `<option value="${s.id}"${s.id === selectedId ? " selected" : ""}>${escapeHtml(s.name)}</option>`
  ).join("");
}

function openAddDoctorModal() {
  const modal = document.createElement("div");
  modal.className = "med-modal med-modal--lg";
  modal.innerHTML = `
    <div class="med-modal__header">
      <h2 class="med-modal__title" id="modal-title">${escapeHtml(t("dashboard.admin.addDoctor"))}</h2>
      <button class="med-modal__close" aria-label="${escapeHtml(t("common.close"))}"><i class="bi bi-x-lg"></i></button>
    </div>
    <form class="med-modal__body adash-form" id="doctor-form">
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.firstName"))}</label><input class="med-input" name="first_name" required></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.lastName"))}</label><input class="med-input" name="last_name" required></div>
      </div>
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.email"))}</label><input class="med-input" type="email" name="email" required></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.phone"))}</label><input class="med-input" name="phone"></div>
      </div>
      <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.password"))}</label><input class="med-input" type="password" name="password" required minlength="8"></div>
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("doctors.directory.filterSpecialty"))}</label><select class="med-select" name="specialization_id" required>${specOptions()}</select></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("dashboard.admin.license"))}</label><input class="med-input" name="license_number" required></div>
      </div>
      <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("payment.confirmation.hospital"))}</label><input class="med-input" name="hospital_name" required></div>
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("doctors.profile.consultationFee"))} (TZS)</label><input class="med-input" type="number" name="consultation_fee" required min="0"></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("landing.popularDoctors.experience", { years: "" }).replace(/\{years\}\s*/, ""))}</label><input class="med-input" type="number" name="experience_years" value="0" min="0"></div>
      </div>
      <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("doctors.profile.education"))}</label><input class="med-input" name="qualification"></div>
    </form>
    <div class="med-modal__footer">
      <button type="button" class="med-btn med-btn--outline-neutral med-modal__close-btn">${escapeHtml(t("common.cancel"))}</button>
      <button type="submit" form="doctor-form" class="med-btn med-btn--primary">${escapeHtml(t("dashboard.admin.addDoctor"))}</button>
    </div>`;

  const backdrop = openModal(modal);
  backdrop.querySelector(".med-modal__close-btn")?.addEventListener("click", closeModal);
  backdrop.querySelector("#doctor-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    body.specialization_id = Number(body.specialization_id);
    body.consultation_fee = Number(body.consultation_fee);
    body.experience_years = Number(body.experience_years || 0);
    try {
      await apiRequest("/admin/dashboard/doctors", { method: "POST", body: JSON.stringify(body) });
      closeModal();
      toast.success(t("toast.success"), t("dashboard.admin.doctorCreated"));
      loadDoctors();
    } catch (err) {
      toast.error(t("toast.createFailed"), err.message);
    }
  });
}

async function openEditDoctorModal(id) {
  const doctors = await apiRequest("/admin/dashboard/doctors");
  const d = doctors.find((x) => x.id === id);
  if (!d) return;

  const modal = document.createElement("div");
  modal.className = "med-modal med-modal--lg";
  modal.innerHTML = `
    <div class="med-modal__header">
      <h2 class="med-modal__title">${escapeHtml(t("common.edit"))} ${escapeHtml(t("common.doctor"))}</h2>
      <button class="med-modal__close" aria-label="${escapeHtml(t("common.close"))}"><i class="bi bi-x-lg"></i></button>
    </div>
    <form class="med-modal__body adash-form" id="edit-doctor-form">
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.firstName"))}</label><input class="med-input" name="first_name" value="${escapeHtml(d.first_name)}" required></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.lastName"))}</label><input class="med-input" name="last_name" value="${escapeHtml(d.last_name)}" required></div>
      </div>
      <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("auth.register.phone"))}</label><input class="med-input" name="phone" value="${escapeHtml(d.phone || "")}"></div>
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("doctors.directory.filterSpecialty"))}</label><select class="med-select" name="specialization_id">${specOptions(d.specialization_id)}</select></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("payment.confirmation.hospital"))}</label><input class="med-input" name="hospital_name" value="${escapeHtml(d.hospital)}"></div>
      </div>
      <div class="med-form-row med-form-row--2">
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("doctors.profile.consultationFee"))} (TZS)</label><input class="med-input" type="number" name="consultation_fee" value="${d.consultation_fee}"></div>
        <div class="med-form-group"><label class="med-form-label">${escapeHtml(t("landing.popularDoctors.experience", { years: "" }).replace(/\{years\}\s*/, ""))}</label><input class="med-input" type="number" name="experience_years" value="${d.experience_years}"></div>
      </div>
      <div class="med-form-group adash-checks">
        <label class="med-check"><input type="checkbox" name="is_verified" class="med-check__input" ${d.is_verified ? "checked" : ""}><span class="med-check__label">${escapeHtml(t("doctors.profile.verified"))}</span></label>
        <label class="med-check"><input type="checkbox" name="is_accepting_patients" class="med-check__input" ${d.is_accepting_patients ? "checked" : ""}><span class="med-check__label">${escapeHtml(t("doctors.profile.acceptingPatients"))}</span></label>
      </div>
    </form>
    <div class="med-modal__footer">
      <button type="button" class="med-btn med-btn--outline-neutral" id="edit-cancel">${escapeHtml(t("common.cancel"))}</button>
      <button type="submit" form="edit-doctor-form" class="med-btn med-btn--primary">${escapeHtml(t("common.save"))}</button>
    </div>`;

  const backdrop = openModal(modal);
  backdrop.querySelector("#edit-cancel")?.addEventListener("click", closeModal);
  backdrop.querySelector("#edit-doctor-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      first_name: fd.get("first_name"),
      last_name: fd.get("last_name"),
      phone: fd.get("phone") || null,
      specialization_id: Number(fd.get("specialization_id")),
      hospital_name: fd.get("hospital_name"),
      consultation_fee: Number(fd.get("consultation_fee")),
      experience_years: Number(fd.get("experience_years")),
      is_verified: fd.get("is_verified") === "on",
      is_accepting_patients: fd.get("is_accepting_patients") === "on",
    };
    try {
      await apiRequest(`/admin/dashboard/doctors/${id}`, { method: "PATCH", body: JSON.stringify(body) });
      closeModal();
      toast.success(t("toast.updated"), t("dashboard.admin.doctorUpdated"));
      loadDoctors();
    } catch (err) {
      toast.error(t("toast.updateFailed"), err.message);
    }
  });
}

async function loadPatients() {
  const container = document.getElementById("adash-patients");
  try {
    const patients = await apiRequest("/admin/dashboard/patients");
    panelData.patients = patients;
    const deactivateLabel = t("toast.deactivated", {}, "Deactivate");
    container.innerHTML = patients.length ? patients.map((p) => `
      <tr>
        <td class="med-table__cell--primary" data-label="${escapeHtml(t("common.patient"))}"><strong>${escapeHtml(p.name)}</strong></td>
        <td data-label="${escapeHtml(t("auth.register.email"))}">${escapeHtml(p.email)}</td>
        <td data-label="${escapeHtml(t("auth.register.phone"))}">${escapeHtml(p.phone || t("common.dash"))}</td>
        <td data-label="${escapeHtml(t("dashboard.admin.nav.appointments"))}">${p.appointment_count}</td>
        <td data-label="${escapeHtml(t("common.status"))}"><span class="med-status med-status--${p.is_active ? "confirmed" : "cancelled"}">${doctorActiveLabel(p.is_active)}</span></td>
        <td class="med-table__cell--actions" data-label="${escapeHtml(t("common.actions"))}">
          ${p.is_active ? `<button type="button" class="med-btn med-btn--warning med-btn--sm" data-deactivate-patient="${p.id}"><i class="bi bi-pause-circle"></i> ${escapeHtml(deactivateLabel)}</button>` : ""}
        </td>
      </tr>
    `).join("") : tableEmptyRow(6, t("dashboard.admin.noPatientsMessage"));

    container.querySelectorAll("[data-deactivate-patient]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm(t("dashboard.admin.deactivatePatient"))) return;
        try {
          await apiRequest(`/admin/dashboard/patients/${btn.dataset.deactivatePatient}/deactivate`, { method: "PATCH" });
          toast.success(t("toast.deactivated"), t("dashboard.admin.patientDeactivated"));
          loadPatients();
        } catch (err) {
          toast.error(t("toast.error"), err.message);
        }
      });
    });
  } catch {
    container.innerHTML = tableEmptyRow(6, t("dashboard.admin.loadError"));
  }
}

async function loadAppointments() {
  const container = document.getElementById("adash-appointments");
  try {
    const items = await apiRequest("/admin/dashboard/appointments");
    panelData.appointments = items;
    container.innerHTML = items.length ? items.map((a) => {
      const statusLabel = appointmentStatus(a.status, a.status_label);
      const statusCls = a.status === "completed" ? "confirmed" : a.status === "cancelled" ? "cancelled" : "scheduled";
      return `
      <tr>
        <td class="med-table__cell--primary" data-label="${escapeHtml(t("common.patient"))}">${escapeHtml(a.patient_name)}</td>
        <td data-label="${escapeHtml(t("common.doctor"))}">${escapeHtml(a.doctor_name)}<br><small>${escapeHtml(a.specialization)}</small></td>
        <td data-label="${escapeHtml(t("booking.stepSummary.date"))}">${escapeHtml(a.date_label)}</td>
        <td data-label="${escapeHtml(t("booking.stepSummary.time"))}">${escapeHtml(a.time_range)}</td>
        <td data-label="${escapeHtml(t("common.status"))}"><span class="med-status med-status--${statusCls}">${escapeHtml(statusLabel)}</span></td>
        <td data-label="${escapeHtml(t("payment.confirmation.paymentStatus"))}">${escapeHtml(a.payment_status || t("common.dash"))}</td>
      </tr>`;
    }).join("") : tableEmptyRow(6, t("dashboard.admin.noAppointments"));
  } catch {
    container.innerHTML = tableEmptyRow(6, t("dashboard.admin.loadError"));
  }
}

async function loadPayments() {
  const container = document.getElementById("adash-payments");
  try {
    const items = await apiRequest("/admin/dashboard/payments");
    panelData.payments = items;
    container.innerHTML = items.length ? items.map((p) => {
      const statusLabel = paymentStatus(p.status, p.status_label);
      return `
      <tr>
        <td class="med-table__cell--primary" data-label="${escapeHtml(t("payment.confirmation.amount"))}">${formatMoney(p.amount, p.currency)}</td>
        <td data-label="${escapeHtml(t("common.patient"))}">${escapeHtml(p.patient_name)}</td>
        <td data-label="${escapeHtml(t("common.doctor"))}">${escapeHtml(p.doctor_name)}</td>
        <td data-label="${escapeHtml(t("payment.simulation.method"))}">${escapeHtml(p.method_label)}</td>
        <td data-label="${escapeHtml(t("common.status"))}"><span class="med-status med-status--${p.status === "completed" ? "confirmed" : "pending"}">${escapeHtml(statusLabel)}</span></td>
        <td data-label="${escapeHtml(t("payment.confirmation.paidAt"))}">${p.paid_at ? formatDate(p.paid_at) : t("common.dash")}</td>
      </tr>`;
    }).join("") : tableEmptyRow(6, t("dashboard.admin.noPayments"));
  } catch {
    container.innerHTML = tableEmptyRow(6, t("dashboard.admin.loadError"));
  }
}

async function loadReports() {
  const container = document.getElementById("adash-reports");
  try {
    const r = await apiRequest("/admin/dashboard/reports");
    panelData.reports = r;
    const charts = r.charts || {};

    container.innerHTML = `
      <p class="adash-report-period">${escapeHtml(t("dashboard.admin.reports.title"))}: <strong>${escapeHtml(r.period_label)}</strong> · ${formatDate(r.generated_at)}</p>
      <div class="adash-stats adash-report-stats">
        ${[
          ["calendar-check", "primary", r.total_appointments, t("dashboard.admin.reports.appointments")],
          ["check-circle", "green", r.completed_appointments, t("dashboard.patient.completed")],
          ["x-circle", "primary", r.cancelled_appointments, t("dashboard.doctor.tabs.cancelled")],
          ["cash-stack", "green", formatMoney(r.total_revenue, r.currency), t("dashboard.admin.monthlyRevenue")],
          ["person-plus", "teal", r.new_patients, t("dashboard.admin.reports.newPatients")],
          ["person-badge", "amber", r.new_doctors, t("dashboard.admin.reports.newDoctors")],
        ].map(([icon, cls, val, label]) => `
          <div class="adash-stat">
            <div class="adash-stat__icon adash-stat__icon--${cls}"><i class="bi bi-${icon}"></i></div>
            <div class="adash-stat__value">${val}</div>
            <div class="adash-stat__label">${label}</div>
          </div>`).join("")}
      </div>

      <div class="adash-report-charts">
        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-pie-chart-fill"></i> ${escapeHtml(t("dashboard.admin.reports.appointmentStatus"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-appt-status"></div></div>
        </section>

        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-credit-card-2-front"></i> ${escapeHtml(t("dashboard.admin.reports.paymentMethods"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-payments"></div></div>
        </section>

        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-bar-chart-fill"></i> ${escapeHtml(t("dashboard.admin.reports.appointmentsTrend"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-appt-trend"></div></div>
        </section>

        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-graph-up-arrow"></i> ${escapeHtml(t("dashboard.admin.reports.revenueTrend"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-revenue"></div></div>
        </section>

        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-pie-chart"></i> ${escapeHtml(t("dashboard.admin.reports.doctorDistribution"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-doctors"></div></div>
        </section>

        <section class="adash-card adash-report-chart-card">
          <header class="adash-card__header">
            <h3 class="adash-card__title"><i class="bi bi-people-fill"></i> ${escapeHtml(t("dashboard.admin.reports.platformGrowth"))}</h3>
          </header>
          <div class="adash-card__body"><div id="report-chart-growth"></div></div>
        </section>
      </div>

      <div class="med-callout adash-report-callout">
        <span class="med-callout__icon"><i class="bi bi-file-earmark-pdf"></i></span>
        <div>
          <strong>${escapeHtml(t("dashboard.admin.reports.comingSoon"))}</strong>
          <p>${escapeHtml(t("dashboard.admin.reports.comingSoon"))}</p>
        </div>
      </div>`;

    const growthItems = (charts.growth_comparison || []).map((item) => ({
      ...item,
      label: item.label === "New Patients"
        ? t("dashboard.admin.reports.newPatients")
        : item.label === "New Doctors"
          ? t("dashboard.admin.reports.newDoctors")
          : item.label,
    }));

    renderPieChart(
      document.getElementById("report-chart-appt-status"),
      charts.appointment_status,
      { emptyMessage: t("dashboard.admin.noDataMessage"), centerLabel: t("dashboard.admin.reports.appointments") }
    );
    renderPieChart(
      document.getElementById("report-chart-payments"),
      charts.payment_methods,
      { emptyMessage: t("dashboard.admin.noDataMessage"), centerLabel: t("dashboard.admin.nav.payments") }
    );
    renderVerticalBarChart(
      document.getElementById("report-chart-appt-trend"),
      charts.appointments_trend,
      { color: "primary", emptyMessage: t("dashboard.admin.noDataMessage") }
    );
    renderVerticalBarChart(
      document.getElementById("report-chart-revenue"),
      charts.revenue_trend,
      { color: "green", emptyMessage: t("dashboard.admin.noDataMessage") }
    );
    renderPieChart(
      document.getElementById("report-chart-doctors"),
      distributionToPieItems(charts.doctor_distribution),
      { emptyMessage: t("dashboard.admin.noDataMessage"), centerLabel: t("dashboard.admin.totalDoctors") }
    );
    renderVerticalBarChart(
      document.getElementById("report-chart-growth"),
      growthItems,
      { color: "teal", emptyMessage: t("dashboard.admin.noDataMessage") }
    );
  } catch {
    container.innerHTML = emptyState("file-earmark-bar-graph", t("dashboard.admin.reports.unavailable"), "");
  }
}

async function loadNotifications() {
  const container = document.getElementById("adash-notifications");
  try {
    const items = await apiRequest("/admin/dashboard/notifications");
    panelData.notifications = items;
    container.innerHTML = items.length ? items.map((n, i) => `
      <div class="adash-notif ${n.is_read ? "adash-notif--read" : ""}" data-reveal-item style="animation-delay:${i * 0.03}s">
        <div class="adash-notif__dot"></div>
        <div>
          <div class="adash-notif__title">${escapeHtml(n.title)} <span class="med-badge med-badge--neutral med-badge--sm">${escapeHtml(n.channel)}</span></div>
          <div class="adash-notif__user">${escapeHtml(n.user_name)}</div>
          <div class="adash-notif__msg">${escapeHtml(n.message)}</div>
        </div>
      </div>
    `).join("") : emptyState("bell-slash", t("dashboard.admin.noNotifications"), "");
    revealStagger(container);
  } catch {
    container.innerHTML = emptyState("exclamation-circle", t("common.empty.loadFailed"), "");
  }
}

async function loadSettings() {
  const container = document.getElementById("adash-settings");
  try {
    const s = await apiRequest("/admin/dashboard/settings");
    panelData.settings = s;
    container.innerHTML = `
      <dl class="adash-settings-list" data-reveal>
        ${[
          [t("dashboard.admin.settings.application"), s.app_name],
          [t("dashboard.admin.settings.environment"), s.environment],
          [t("dashboard.admin.currency"), s.currency],
          [t("dashboard.admin.settings.remindersEnabled"), s.reminder_enabled ? t("common.yes") : t("common.no")],
          [t("dashboard.admin.settings.reminderInterval"), t("dashboard.admin.settings.minutes", { count: s.reminder_check_interval_minutes })],
          [t("dashboard.admin.settings.reminderWindow"), t("dashboard.admin.settings.hoursBefore", { count: s.reminder_hours_before })],
          [t("dashboard.admin.settings.emailReminders"), s.email_reminders_enabled ? t("dashboard.admin.settings.enabled") : t("dashboard.admin.settings.disabled")],
        ].map(([k, v]) => `<div><dt>${k}</dt><dd>${escapeHtml(String(v))}</dd></div>`).join("")}
      </dl>`;
  } catch {
    container.innerHTML = emptyState("gear", t("dashboard.admin.settings.unavailable"), "");
  }
}

function rerenderActivePanels() {
  updatePageTitle(activePanel);
  if (overviewData) renderOverview(overviewData);
  const loaders = {
    doctors: loadDoctors,
    patients: loadPatients,
    appointments: loadAppointments,
    payments: loadPayments,
    reports: loadReports,
    notifications: loadNotifications,
    settings: loadSettings,
  };
  loaders[activePanel]?.();
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initSidebar();

  document.querySelectorAll(".adash-nav__btn").forEach((btn) => {
    btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
  });
  document.getElementById("btn-add-doctor")?.addEventListener("click", openAddDoctorModal);

  try {
    specializations = await apiRequest("/admin/dashboard/specializations");
    const overview = await apiRequest("/admin/dashboard/overview");
    renderOverview(overview);
    updatePageTitle("overview");
  } catch {
    toast.error(t("toast.dashboardError"), t("dashboard.admin.loadError"));
  }

  onLanguageChange(rerenderActivePanels);
});
