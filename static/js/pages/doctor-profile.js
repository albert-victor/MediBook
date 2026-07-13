/**
 * Doctor Profile - dynamic profile page
 */

import { apiRequest } from "../utils/api.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { t } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";

let profileData = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatFee(amount, currency) {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function stars(rating) {
  return Array.from({ length: 5 }, (_, i) =>
    `<i class="bi bi-star${i < rating ? "-fill" : ""}"></i>`
  ).join("");
}

function renderProfile(d) {
  document.title = `${d.name} - mediBook`;

  const visual = document.getElementById("profile-visual");
  if (visual) {
    visual.innerHTML = d.image_url
      ? `<img src="${escapeHtml(d.image_url)}" alt="${escapeHtml(d.name)}" class="doctor-profile-page__photo">`
      : `<div class="doctor-profile-page__avatar doctor-profile-page__avatar--${d.avatar_gradient}">${escapeHtml(d.initials)}</div>`;
  }

  const badges = document.getElementById("profile-badges");
  if (badges) {
    badges.innerHTML = `
      ${d.is_verified ? `<span class="med-badge med-badge--success"><i class="bi bi-patch-check"></i> ${t("doctors.profile.verified")}</span>` : ""}
      ${d.available_today ? `<span class="med-badge med-badge--accent"><span class="med-status-dot med-status-dot--success med-status-dot--pulse"></span> ${t("landing.popularDoctors.availableToday")}</span>` : ""}
    `;
  }

  document.getElementById("profile-name").textContent = d.name;
  document.getElementById("profile-specialty").textContent = d.specialization;
  document.getElementById("profile-qualification").textContent = d.qualification;
  document.getElementById("profile-bio").textContent = d.bio;

  const meta = document.getElementById("profile-meta");
  if (meta) {
    meta.innerHTML = `
      <span><i class="bi bi-star-fill"></i> ${d.rating.toFixed(1)} (${t("landing.popularDoctors.reviews", { count: d.review_count })})</span>
      <span><i class="bi bi-briefcase"></i> ${t("landing.popularDoctors.experience", { years: d.experience_years })}</span>
      <span><i class="bi bi-geo-alt"></i> ${escapeHtml(d.hospital)}</span>
    `;
  }

  const bookBtn = document.getElementById("profile-book-btn");
  if (bookBtn) {
    bookBtn.href = d.book_url;
    bookBtn.textContent = t("doctors.profile.bookAppointment");
  }

  const fee = document.getElementById("profile-fee");
  if (fee) fee.innerHTML = `<span>${t("doctors.profile.consultationFee")}</span><strong>${formatFee(d.fee, d.currency)}</strong>`;

  const education = document.getElementById("profile-education");
  if (education) {
    education.innerHTML = d.education.length
      ? d.education.map((e) => `<li><i class="bi bi-check-circle-fill"></i> ${escapeHtml(e)}</li>`).join("")
      : `<li>${t("common.empty.noData")}</li>`;
  }

  const schedule = document.getElementById("profile-schedule");
  if (schedule) {
    schedule.innerHTML = `
      <div class="doctor-profile-page__schedule-row">
        <span class="doctor-profile-page__schedule-label"><i class="bi bi-calendar-week"></i> ${t("doctors.profile.schedule")}</span>
        <div class="doctor-profile-page__tags">
          ${d.working_days.map((day) => `<span class="med-pill">${escapeHtml(day)}</span>`).join("")}
        </div>
      </div>
      <div class="doctor-profile-page__schedule-row">
        <span class="doctor-profile-page__schedule-label"><i class="bi bi-clock"></i> ${t("doctors.profile.schedule")}</span>
        <strong>${escapeHtml(d.working_hours)}</strong>
      </div>
    `;
  }

  const languages = document.getElementById("profile-languages");
  if (languages) {
    languages.innerHTML = d.languages.map((lang) => `<span class="med-pill">${escapeHtml(lang)}</span>`).join("");
  }

  const reviews = document.getElementById("profile-reviews");
  if (reviews) {
    reviews.innerHTML = d.reviews.length
      ? d.reviews.map((r, i) => `
          <article class="doctor-profile-page__review" data-reveal-item style="transition-delay:${i * 60}ms">
            <div class="doctor-profile-page__review-head">
              <strong>${escapeHtml(r.patient_name)}</strong>
              <span class="doctor-profile-page__review-stars">${stars(r.rating)}</span>
            </div>
            <p>${escapeHtml(r.comment)}</p>
          </article>
        `).join("")
      : `<p class="doctor-profile-page__muted">${t("common.empty.noData")}</p>`;
  }

  const calendar = document.getElementById("profile-calendar");
  if (calendar) {
    const daysWithSlots = d.availability_calendar.filter((day) => day.slots.length > 0);
    calendar.innerHTML = daysWithSlots.length
      ? daysWithSlots.slice(0, 7).map((day) => `
          <div class="doctor-profile-page__cal-day">
            <div class="doctor-profile-page__cal-date">${escapeHtml(day.label)}</div>
            <div class="doctor-profile-page__cal-slots">
              ${day.slots.map((s) => `<span class="doctor-profile-page__cal-slot">${s.start_time}</span>`).join("")}
            </div>
          </div>
        `).join("")
      : `<p class="doctor-profile-page__muted">${t("landing.availableToday.noSameDayMessage")}</p>`;
  }

  document.getElementById("profile-loading").hidden = true;
  document.getElementById("profile-content").hidden = false;
  initScrollReveal();
}

async function loadProfile() {
  const page = document.getElementById("doctor-profile-page");
  const doctorId = page?.dataset.doctorId;
  if (!doctorId) return;

  try {
    profileData = await apiRequest(`/doctors/${doctorId}`);
    renderProfile(profileData);
  } catch {
    document.getElementById("profile-loading").hidden = true;
    document.getElementById("profile-error").hidden = false;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollReveal();
  loadProfile();
  onLanguageChange(() => {
    if (profileData) renderProfile(profileData);
  });
});
