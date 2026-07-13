/**
 * Patient Dashboard - dynamic data loading via Fetch API
 * No page reloads; staggered card animations
 */

import { apiRequest } from "../utils/api.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { t, formatDate, formatTime, timeAgo, translateGreeting } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";
import { appointmentStatus, paymentStatus } from "../i18n/statusLabels.js";

const STATUS_CLASS = {
  pending: "pending",
  scheduled: "scheduled",
  confirmed: "confirmed",
  completed: "completed",
  cancelled: "cancelled",
  no_show: "cancelled",
};

const GRADIENT_CLASS = {
  primary: "primary",
  teal: "teal",
  green: "green",
  amber: "amber",
};

let dashboardData = null;

/** @param {string} iso */
function formatDateParts(iso) {
  const d = new Date(iso);
  return {
    month: formatDate(d, { month: "short" }),
    day: d.getDate(),
  };
}

/** @param {number} amount @param {string} currency */
function formatMoney(amount, currency) {
  return `${currency} ${amount.toLocaleString()}`;
}

/** @param {HTMLElement} container */
function revealStagger(container) {
  if (!container) return;
  container.querySelectorAll("[data-reveal-item], .pdash-stat, .pdash-action, .pdash-appt-item, .pdash-payment-item, .pdash-notif, .pdash-doctor").forEach((el, i) => {
    el.style.animationDelay = `${i * 0.07}s`;
  });
  initScrollReveal();
}

/** @param {string} html */
function emptyState(icon, title, subtitle) {
  return `
    <div class="med-empty med-empty--compact">
      <div class="med-empty__illustration"><i class="bi bi-${icon}"></i></div>
      <p class="med-empty__title">${title}</p>
      <p class="med-empty__subtitle">${subtitle}</p>
    </div>`;
}

/** @param {import('../utils/api.js').DashboardOverview} data */
function renderOverview(data) {
  const greeting = document.getElementById("pdash-greeting");
  const nameEl = document.getElementById("pdash-patient-name");
  const profileName = document.getElementById("pdash-profile-name");
  if (greeting) greeting.textContent = translateGreeting(data.greeting);
  if (nameEl) nameEl.textContent = data.patient_name;
  if (profileName) profileName.textContent = data.patient_name;

  renderStats(data.stats);
  renderUpcoming(data.upcoming);
  renderReminder(data.reminder);
  renderQuickActions(data.quick_actions);
  updateNotifyBadge(data.stats.unread_notifications);
}

/** @param {object} stats */
function renderStats(stats) {
  const container = document.getElementById("pdash-stats");
  if (!container) return;

  const items = [
    { icon: "calendar-check", cls: "primary", value: stats.total_appointments, label: t("dashboard.patient.totalVisits") },
    { icon: "check-circle", cls: "green", value: stats.completed, label: t("dashboard.patient.completed") },
    { icon: "calendar-event", cls: "teal", value: stats.upcoming, label: t("dashboard.patient.upcoming") },
    { icon: "cash-stack", cls: "amber", value: formatMoney(stats.total_spent, stats.currency), label: t("dashboard.patient.totalSpent") },
  ];

  container.innerHTML = items.map((s, i) => `
    <div class="pdash-stat" data-reveal-item style="animation-delay:${i * 0.08}s">
      <div class="pdash-stat__icon pdash-stat__icon--${s.cls}"><i class="bi bi-${s.icon}"></i></div>
      <div class="pdash-stat__value">${s.value}</div>
      <div class="pdash-stat__label">${s.label}</div>
    </div>
  `).join("");

  revealStagger(container);
}

/** @param {object|null} upcoming */
function renderUpcoming(upcoming) {
  const container = document.getElementById("pdash-upcoming");
  if (!container) return;

  if (!upcoming) {
    container.innerHTML = emptyState(
      "calendar-x",
      t("dashboard.patient.noUpcomingTitle"),
      t("dashboard.patient.noUpcomingMessage")
    );
    return;
  }

  const parts = formatDateParts(upcoming.scheduled_start);
  const statusCls = STATUS_CLASS[upcoming.status] || "scheduled";
  const statusLabel = appointmentStatus(upcoming.status, upcoming.status_label);
  const countdown = upcoming.days_until > 0
    ? t("dashboard.patient.countdownDays", { count: upcoming.days_until })
    : t("dashboard.patient.countdownHours", { count: upcoming.hours_until });

  container.innerHTML = `
    <div class="pdash-upcoming">
      <div class="pdash-upcoming__date">
        <div class="pdash-upcoming__month">${parts.month}</div>
        <div class="pdash-upcoming__day">${parts.day}</div>
      </div>
      <div class="pdash-upcoming__details">
        <div class="pdash-upcoming__doctor">${escapeHtml(upcoming.doctor_name)}</div>
        <div class="pdash-upcoming__meta">
          ${escapeHtml(upcoming.specialization)} · ${escapeHtml(upcoming.hospital)}<br>
          ${formatDate(upcoming.scheduled_start)} · ${formatTime(upcoming.scheduled_start)}
        </div>
        <span class="med-status med-status--${statusCls}">${escapeHtml(statusLabel)}</span>
        <div class="pdash-upcoming__countdown med-mt-3">
          <i class="bi bi-hourglass-split"></i>
          ${countdown}
        </div>
      </div>
    </div>`;
}

/** @param {object|null} reminder */
function renderReminder(reminder) {
  const section = document.getElementById("reminder-section");
  const container = document.getElementById("pdash-reminder");
  if (!section || !container) return;

  if (!reminder) {
    section.hidden = true;
    return;
  }

  section.hidden = false;
  container.innerHTML = `
    <div class="pdash-reminder__title">${escapeHtml(reminder.title)}</div>
    <div class="pdash-reminder__message">${escapeHtml(reminder.message)}</div>
  `;
}

/** @param {Array} actions */
function renderQuickActions(actions) {
  const container = document.getElementById("pdash-quick-actions");
  if (!container) return;

  const actionLabels = {
    book: t("dashboard.patient.bookAppointment"),
    find: t("dashboard.patient.findDoctor"),
    payments: t("dashboard.patient.paymentHistory"),
    help: t("dashboard.patient.getHelp"),
  };

  container.innerHTML = actions.map((a, i) => `
    <a href="${escapeHtml(a.url)}" class="pdash-action" data-reveal-item style="animation-delay:${i * 0.06}s">
      <div class="pdash-action__icon pdash-action__icon--${a.color}"><i class="bi ${a.icon}"></i></div>
      <span class="pdash-action__label">${escapeHtml(actionLabels[a.id] || a.label)}</span>
    </a>
  `).join("");

  container.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const id = link.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  revealStagger(container);
}

/** @param {Array} appointments */
function renderAppointments(appointments) {
  const container = document.getElementById("pdash-appointments");
  if (!container) return;

  if (!appointments.length) {
    container.innerHTML = emptyState(
      "journal-medical",
      t("dashboard.patient.noAppointmentsTitle"),
      t("dashboard.patient.noAppointmentsMessage")
    );
    return;
  }

  container.innerHTML = appointments.map((a, i) => {
    const grad = ["primary", "teal", "green", "amber"][i % 4];
    const initials = a.doctor_name.replace("Dr. ", "").split(" ").map((p) => p[0]).join("").slice(0, 2);
    const statusCls = STATUS_CLASS[a.status] || "scheduled";
    const statusLabel = appointmentStatus(a.status, a.status_label);
    const payBtn = a.payment_url
      ? `<a href="${escapeHtml(a.payment_url)}" class="med-btn med-btn--primary med-btn--sm pdash-appt-item__pay">${t("payment.payNow")}</a>`
      : "";
    return `
      <div class="pdash-appt-item" data-reveal-item style="animation-delay:${i * 0.05}s">
        <div class="pdash-appt-item__avatar pdash-appt-item__avatar--${grad}">${initials}</div>
        <div class="pdash-appt-item__info">
          <div class="pdash-appt-item__name">${escapeHtml(a.doctor_name)}</div>
          <div class="pdash-appt-item__meta">${escapeHtml(a.specialization)} · <span class="med-status med-status--${statusCls}">${escapeHtml(statusLabel)}</span></div>
        </div>
        <div class="pdash-appt-item__aside">
          <div class="pdash-appt-item__date">${formatDate(a.scheduled_start)}<br>${formatTime(a.scheduled_start)}</div>
          ${payBtn}
        </div>
      </div>`;
  }).join("");

  revealStagger(container);
}

/** @param {Array} payments */
function renderPayments(payments) {
  const container = document.getElementById("pdash-payments");
  if (!container) return;

  if (!payments.length) {
    container.innerHTML = emptyState(
      "credit-card",
      t("dashboard.patient.noPaymentsTitle"),
      t("dashboard.patient.noPaymentsMessage")
    );
    return;
  }

  container.innerHTML = payments.map((p, i) => {
    const statusCls = p.status === "completed" ? "confirmed" : p.status === "pending" ? "pending" : "cancelled";
    const statusLabel = paymentStatus(p.status, p.status_label);
    return `
      <div class="pdash-payment-item" data-reveal-item style="animation-delay:${i * 0.05}s">
        <div class="pdash-payment-item__left">
          <div class="pdash-payment-item__icon"><i class="bi bi-phone"></i></div>
          <div>
            <div class="pdash-payment-item__doctor">${escapeHtml(p.doctor_name)}</div>
            <div class="pdash-payment-item__ref">${escapeHtml(p.method_label)} · ${escapeHtml(p.reference_number)}</div>
          </div>
        </div>
        <div>
          <div class="pdash-payment-item__amount">${formatMoney(p.amount, p.currency)}</div>
          <span class="med-status med-status--${statusCls}">${escapeHtml(statusLabel)}</span>
        </div>
      </div>`;
  }).join("");

  revealStagger(container);
}

/** @param {Array} notifications */
function renderNotifications(notifications) {
  const container = document.getElementById("pdash-notifications");
  const countBadge = document.getElementById("pdash-notif-count");
  if (!container) return;

  const unread = notifications.filter((n) => !n.is_read).length;
  if (countBadge) {
    countBadge.hidden = unread === 0;
    countBadge.textContent = `${unread} new`;
  }
  updateNotifyBadge(unread);

  if (!notifications.length) {
    container.innerHTML = emptyState(
      "bell-slash",
      t("dashboard.patient.allCaughtUp"),
      t("dashboard.patient.noNotifications")
    );
    return;
  }

  container.innerHTML = notifications.map((n, i) => {
    const meta = n.doctor_name
      ? `<div class="pdash-notif__meta">${escapeHtml(n.doctor_name)}${n.department ? ` · ${escapeHtml(n.department)}` : ""}${n.appointment_date ? ` · ${escapeHtml(n.appointment_date)}` : ""}${n.appointment_time ? ` · ${escapeHtml(n.appointment_time)}` : ""}</div>`
      : "";
    const channel = n.channel_label
      ? `<span class="med-badge med-badge--neutral med-badge--sm pdash-notif__channel">${escapeHtml(n.channel_label)}</span>`
      : "";
    return `
    <div class="pdash-notif ${n.is_read ? "pdash-notif--read" : "pdash-notif--unread"}"
         data-notif-id="${n.id}" data-reveal-item style="animation-delay:${i * 0.04}s" role="button" tabindex="0">
      <div class="pdash-notif__dot"></div>
      <div>
        <div class="pdash-notif__head">
          <div class="pdash-notif__title">${escapeHtml(n.title)}</div>
          ${channel}
        </div>
        ${meta}
        <div class="pdash-notif__message">${escapeHtml(n.message)}</div>
        <div class="pdash-notif__time">${timeAgo(n.created_at)}</div>
      </div>
    </div>
  `;
  }).join("");

  container.querySelectorAll(".pdash-notif").forEach((el) => {
    const handler = () => markRead(Number(el.dataset.notifId), el);
    el.addEventListener("click", handler);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handler();
      }
    });
  });

  revealStagger(container);
}

/** @param {Array} doctors */
function renderDoctors(containerId, doctors, showBook = true) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!doctors.length) {
    const msg = containerId.includes("recent")
      ? ["people", t("dashboard.patient.noRecentDoctors"), t("dashboard.patient.noRecentDoctorsMessage")]
      : ["person-x", t("dashboard.patient.noDoctorsAvailable"), t("dashboard.patient.noDoctorsAvailableMessage")];
    container.innerHTML = emptyState(...msg);
    return;
  }

  container.innerHTML = doctors.map((d, i) => {
    const grad = GRADIENT_CLASS[d.avatar_gradient] || "primary";
    const avail = d.available_today
      ? `<span class="med-badge med-badge--success med-badge--sm"><i class="bi bi-circle-fill" style="font-size:6px"></i> ${t("landing.popularDoctors.availableToday")}</span>`
      : `<span class="med-badge med-badge--neutral med-badge--sm">${t("landing.popularDoctors.nextTomorrow")}</span>`;
    return `
      <div class="pdash-doctor" data-reveal-item style="animation-delay:${i * 0.06}s">
        <div class="pdash-doctor__avatar pdash-doctor__avatar--${grad}">${escapeHtml(d.initials)}</div>
        <div class="pdash-doctor__info">
          <div class="pdash-doctor__name">${escapeHtml(d.name)}</div>
          <div class="pdash-doctor__spec">${escapeHtml(d.specialization)} · ${escapeHtml(d.hospital)}</div>
          <div class="pdash-doctor__fee">${formatMoney(d.fee, d.currency)}</div>
        </div>
        <div class="pdash-doctor__actions">
          ${showBook ? avail : ""}
          <a href="${escapeHtml(d.book_url)}" class="med-btn med-btn--primary med-btn--sm">${t("landing.popularDoctors.bookAppointment")}</a>
        </div>
      </div>`;
  }).join("");

  revealStagger(container);
}

/** @param {number} count */
function updateNotifyBadge(count) {
  const badge = document.getElementById("pdash-notify-badge");
  if (!badge) return;
  badge.hidden = count === 0;
  badge.textContent = count > 9 ? "9+" : String(count);
}

/** @param {number} id @param {HTMLElement} el */
async function markRead(id, el) {
  if (el.classList.contains("pdash-notif--read")) return;
  try {
    await apiRequest(`/patient/notifications/${id}/read`, { method: "PATCH" });
    el.classList.remove("pdash-notif--unread");
    el.classList.add("pdash-notif--read");
    const badge = document.getElementById("pdash-notify-badge");
    if (badge && !badge.hidden) {
      const n = Math.max(0, parseInt(badge.textContent, 10) - 1);
      updateNotifyBadge(n);
    }
    const countEl = document.getElementById("pdash-notif-count");
    if (countEl && !countEl.hidden) {
      const m = countEl.textContent.match(/(\d+)/);
      if (m) {
        const left = Math.max(0, parseInt(m[1], 10) - 1);
        countEl.hidden = left === 0;
        countEl.textContent = `${left} new`;
      }
    }
  } catch {
    /* silent - user can retry */
  }
}

function renderAll(data) {
  renderOverview(data.overview);
  renderAppointments(data.appointments);
  renderPayments(data.payments);
  renderNotifications(data.notifications);
  renderDoctors("pdash-available-doctors", data.available, true);
  renderDoctors("pdash-recent-doctors", data.recent, false);
}

/** @param {string} str */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadDashboard() {
  try {
    const [overview, appointments, payments, notifications, available, recent] = await Promise.all([
      apiRequest("/patient/dashboard/overview"),
      apiRequest("/patient/dashboard/appointments"),
      apiRequest("/patient/dashboard/payments"),
      apiRequest("/patient/dashboard/notifications"),
      apiRequest("/patient/dashboard/doctors/available"),
      apiRequest("/patient/dashboard/doctors/recent"),
    ]);

    dashboardData = { overview, appointments, payments, notifications, available, recent };
    renderAll(dashboardData);
  } catch (err) {
    console.error("Dashboard load failed:", err);
    const main = document.getElementById("pdash-main");
    if (main) {
      const alert = document.createElement("div");
      alert.className = "med-alert med-alert--danger med-container med-mt-6";
      alert.setAttribute("role", "alert");
      alert.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${t("dashboard.patient.loadError")}`;
      main.prepend(alert);
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();

  document.getElementById("pdash-notify-btn")?.addEventListener("click", () => {
    document.getElementById("notifications-section")?.scrollIntoView({ behavior: "smooth" });
  });

  loadDashboard();
  onLanguageChange(() => {
    if (dashboardData) renderAll(dashboardData);
  });
});
