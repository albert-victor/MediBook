/**
 * Doctor Directory - dynamic listing with instant search & filters
 */

import { apiRequest } from "../utils/api.js";
import { initScrollReveal } from "../utils/scroll-reveal.js";
import { t } from "../i18n/translator.js";
import { onLanguageChange, i18nReady } from "../i18n/languageManager.js";

/** @type {Array} */
let allDoctors = [];
/** @type {object|null} */
let meta = null;

const state = {
  q: "",
  specialty: "",
  availability: "",
  gender: "",
  feeId: "any",
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatFee(amount, currency) {
  return `${currency} ${Math.round(amount).toLocaleString()}`;
}

function readUrlParams() {
  const params = new URLSearchParams(window.location.search);
  state.q = params.get("q") || "";
  state.specialty = params.get("specialty") || params.get("specialization") || "";
  const searchInput = document.querySelector("#doctors-directory-search .med-search__input");
  const searchSelect = document.querySelector("#doctors-directory-search .med-search-block__select");
  if (searchInput && state.q) searchInput.value = state.q;
  if (searchSelect && state.specialty) searchSelect.value = state.specialty;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  if (state.specialty) params.set("specialty", state.specialty);
  const qs = params.toString();
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState({}, "", url);
}

function syncQuickPills() {
  document.querySelectorAll(".doctors-page__quick-pill").forEach((pill) => {
    pill.classList.toggle("is-active", pill.dataset.specialty === state.specialty);
  });
}

function hasActiveFilters() {
  return Boolean(
    state.q ||
    state.specialty ||
    state.availability ||
    state.gender ||
    (state.feeId && state.feeId !== "any")
  );
}

function updateResultsCount(filteredCount) {
  const countEl = document.getElementById("doctors-results-count");
  const clearBtn = document.getElementById("doctors-results-clear");
  if (!countEl) return;

  const total = allDoctors.length;

  if (!hasActiveFilters()) {
    countEl.textContent = t("doctors.directory.showingAll", { count: total });
    countEl.classList.remove("is-filtered");
    if (clearBtn) clearBtn.hidden = true;
  } else {
    countEl.textContent = t("doctors.directory.resultsFiltered", { count: filteredCount, total });
    countEl.classList.add("is-filtered");
    if (clearBtn) clearBtn.hidden = false;
  }
}

function getFeeRange() {
  if (!meta) return { min: 0, max: 999999999 };
  const range = meta.fee_ranges.find((r) => r.id === state.feeId);
  return range ? { min: range.min, max: range.max } : { min: 0, max: 999999999 };
}

function applyClientFilters() {
  const fee = getFeeRange();
  return allDoctors.filter((d) => {
    if (state.q) {
      const q = state.q.toLowerCase();
      const hay = `${d.name} ${d.specialization} ${d.hospital} ${d.qualification}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (state.specialty) {
      const s = state.specialty.toLowerCase();
      if (d.specialization.toLowerCase() !== s && d.specialization_slug !== s.replace(/ /g, "-")) return false;
    }
    if (state.availability === "today" && !d.available_today) return false;
    if (state.availability === "week" && !d.available_today && !d.availability_label.toLowerCase().includes("week")) return false;
    if (state.gender && d.gender !== state.gender) return false;
    if (d.fee < fee.min || d.fee > fee.max) return false;
    return true;
  });
}

function renderCard(doctor, index) {
  const availClass = doctor.available_today ? "is-available" : "";
  const liveDot = doctor.available_today
    ? `<span class="dir-doctor-card__live" title="${t("doctors.directory.availableToday")}"></span>`
    : "";

  return `
    <article class="dir-doctor-card" style="animation-delay:${Math.min(index, 12) * 40}ms">
      <div class="dir-doctor-card__inner">
        <div class="dir-doctor-card__visual">
          ${
            doctor.image_url
              ? `<img class="dir-doctor-card__image" src="${escapeHtml(doctor.image_url)}" alt="" loading="lazy">`
              : `<div class="dir-doctor-card__avatar dir-doctor-card__avatar--${doctor.avatar_gradient}" aria-hidden="true">${escapeHtml(doctor.initials)}</div>`
          }
          ${liveDot}
        </div>
        <div class="dir-doctor-card__body">
          <div class="dir-doctor-card__name-row">
            <h3 class="dir-doctor-card__name">
              <a href="${escapeHtml(doctor.profile_url)}">${escapeHtml(doctor.name)}</a>
            </h3>
            <span class="dir-doctor-card__badge"><i class="bi bi-patch-check-fill" aria-hidden="true"></i> ${t("doctors.profile.verified")}</span>
          </div>
          <p class="dir-doctor-card__specialty">${escapeHtml(doctor.specialization)}</p>
          <p class="dir-doctor-card__hospital"><i class="bi bi-hospital-fill" aria-hidden="true"></i> ${escapeHtml(doctor.hospital)}</p>
          <div class="dir-doctor-card__meta">
            <span class="dir-doctor-card__rating"><i class="bi bi-star-fill" aria-hidden="true"></i> ${doctor.rating.toFixed(1)}</span>
            <span><i class="bi bi-briefcase-fill" aria-hidden="true"></i> ${t("landing.popularDoctors.experience", { years: doctor.experience_years })}</span>
            <span class="dir-doctor-card__availability ${availClass}">${escapeHtml(doctor.availability_label)}</span>
          </div>
        </div>
      </div>
      <div class="dir-doctor-card__footer">
        <span class="dir-doctor-card__fee">${formatFee(doctor.fee, doctor.currency)}</span>
        <div class="dir-doctor-card__actions">
          <a href="${escapeHtml(doctor.profile_url)}" class="med-btn med-btn--outline-neutral med-btn--sm">${t("doctors.directory.viewShort")}</a>
          <a href="${escapeHtml(doctor.book_url)}" class="med-btn med-btn--primary med-btn--sm" title="${t("landing.popularDoctors.bookAppointment")}"><i class="bi bi-calendar2-plus-fill" aria-hidden="true"></i> ${t("doctors.directory.bookShort")}</a>
        </div>
      </div>
    </article>`;
}

function renderDoctors() {
  const grid = document.getElementById("doctors-grid");
  const empty = document.getElementById("doctors-empty");
  if (!grid) return;

  const filtered = applyClientFilters();
  syncQuickPills();
  updateResultsCount(filtered.length);

  if (!filtered.length) {
    grid.innerHTML = "";
    grid.hidden = true;
    if (empty) empty.hidden = false;
    return;
  }

  if (empty) empty.hidden = true;
  grid.hidden = false;
  grid.innerHTML = filtered.map((d, i) => renderCard(d, i)).join("");
}

function populateQuickFilters() {
  const container = document.getElementById("doctors-quick-filters");
  if (!container || !meta) return;

  const top = meta.specializations
    .filter((s) => s.doctor_count > 0)
    .sort((a, b) => b.doctor_count - a.doctor_count)
    .slice(0, 5);

  if (!top.length) return;

  container.hidden = false;
  container.querySelectorAll(".doctors-page__quick-pill").forEach((el) => el.remove());

  top.forEach((spec) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "doctors-page__quick-pill";
    btn.dataset.specialty = spec.name;
    btn.textContent = spec.name;
    btn.addEventListener("click", () => {
      state.specialty = state.specialty === spec.name ? "" : spec.name;
      const specSelect = document.getElementById("filter-specialty");
      const searchSelect = document.querySelector("#doctors-directory-search .med-search-block__select");
      if (specSelect) specSelect.value = state.specialty;
      if (searchSelect) searchSelect.value = state.specialty;
      syncUrl();
      renderDoctors();
    });
    container.appendChild(btn);
  });

  syncQuickPills();
}

function populateFilters() {
  if (!meta) return;

  const specSelect = document.getElementById("filter-specialty");
  if (specSelect) {
    meta.specializations
      .filter((s) => s.doctor_count > 0)
      .forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.name;
        opt.textContent = `${s.name} (${s.doctor_count})`;
        if (state.specialty && state.specialty.toLowerCase() === s.name.toLowerCase()) opt.selected = true;
        specSelect.appendChild(opt);
      });
  }

  const feeSelect = document.getElementById("filter-fee");
  if (feeSelect) {
    meta.fee_ranges.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r.id;
      opt.textContent = r.label;
      feeSelect.appendChild(opt);
    });
  }

  document.getElementById("doctors-total").textContent = String(meta.total);
  document.getElementById("doctors-specialties").textContent = String(
    meta.specializations.filter((s) => s.doctor_count > 0).length
  );

  populateQuickFilters();
}

function updateAvailableCount() {
  const el = document.getElementById("doctors-available");
  if (el) el.textContent = String(allDoctors.filter((d) => d.available_today).length);
}

function bindEvents() {
  const searchForm = document.querySelector("#doctors-directory-search form");
  const searchInput = document.querySelector("#doctors-directory-search .med-search__input");
  const searchSelect = document.querySelector("#doctors-directory-search .med-search-block__select");

  searchForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    state.q = searchInput?.value.trim() || "";
    state.specialty = searchSelect?.value || state.specialty;
    syncUrl();
    renderDoctors();
  });

  searchInput?.addEventListener("input", () => {
    state.q = searchInput.value.trim();
    syncUrl();
    renderDoctors();
  });

  searchSelect?.addEventListener("change", (e) => {
    state.specialty = e.target.value;
    const specSelect = document.getElementById("filter-specialty");
    if (specSelect) specSelect.value = state.specialty;
    syncUrl();
    renderDoctors();
  });

  document.getElementById("filter-specialty")?.addEventListener("change", (e) => {
    state.specialty = e.target.value;
    if (searchSelect) searchSelect.value = state.specialty;
    syncUrl();
    renderDoctors();
  });

  document.getElementById("filter-availability")?.addEventListener("change", (e) => {
    state.availability = e.target.value;
    renderDoctors();
  });

  document.getElementById("filter-fee")?.addEventListener("change", (e) => {
    state.feeId = e.target.value;
    renderDoctors();
  });

  document.querySelectorAll(".doctors-page__chip[data-gender]").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".doctors-page__chip[data-gender]").forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      state.gender = chip.dataset.gender || "";
      renderDoctors();
    });
  });

  const clearFilters = () => {
    state.q = "";
    state.specialty = "";
    state.availability = "";
    state.gender = "";
    state.feeId = "any";
    if (searchInput) searchInput.value = "";
    if (searchSelect) searchSelect.value = "";
    document.getElementById("filter-specialty").value = "";
    document.getElementById("filter-availability").value = "";
    document.getElementById("filter-fee").value = "any";
    document.querySelectorAll(".doctors-page__chip[data-gender]").forEach((c) => {
      c.classList.toggle("is-active", c.dataset.gender === "");
    });
    syncUrl();
    renderDoctors();
  };

  document.getElementById("doctors-clear-filters")?.addEventListener("click", clearFilters);
  document.getElementById("doctors-empty-reset")?.addEventListener("click", clearFilters);
  document.getElementById("doctors-results-clear")?.addEventListener("click", clearFilters);

  document.getElementById("doctors-filters-toggle")?.addEventListener("click", () => {
    const panel = document.getElementById("doctors-filters");
    const btn = document.getElementById("doctors-filters-toggle");
    if (!panel || !btn) return;
    const open = panel.classList.toggle("is-open");
    btn.setAttribute("aria-expanded", String(open));
  });
}

async function loadDoctors() {
  try {
    [allDoctors, meta] = await Promise.all([
      apiRequest("/doctors"),
      apiRequest("/doctors/meta"),
    ]);
    populateFilters();
    updateAvailableCount();
    renderDoctors();
  } catch (err) {
    console.error(err);
    const grid = document.getElementById("doctors-grid");
    if (grid) {
      grid.hidden = false;
      grid.innerHTML = `<div class="med-alert med-alert--danger">${t("booking.loadDoctorsFailed")}</div>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  readUrlParams();
  bindEvents();
  initScrollReveal();
  loadDoctors();
  onLanguageChange(() => {
    if (allDoctors.length) renderDoctors();
  });
});
