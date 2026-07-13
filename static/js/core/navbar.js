/**
 * Global top navigation - mobile drawer toggle (all public pages)
 */

import { t } from "../i18n/translator.js";
import { onLanguageChange } from "../i18n/languageManager.js";

let mobileNavToggle = null;
let mobileNavPanel = null;
let mobileNavBackdrop = null;
let mobileNavOpen = false;

function updateMobileNavAria() {
  if (!mobileNavToggle) return;
  mobileNavToggle.setAttribute(
    "aria-label",
    mobileNavOpen ? t("navigation.closeMenu") : t("navigation.openMenu")
  );
}

export function closeMobileNav() {
  if (!mobileNavPanel || !mobileNavToggle) return;
  mobileNavPanel.classList.remove("is-open");
  mobileNavPanel.setAttribute("aria-hidden", "true");
  mobileNavBackdrop?.classList.remove("is-open");
  mobileNavBackdrop?.setAttribute("aria-hidden", "true");
  mobileNavOpen = false;
  mobileNavToggle.setAttribute("aria-expanded", "false");
  document.documentElement.classList.remove("med-nav-open");
  document.body.classList.remove("med-nav-open");
  updateMobileNavAria();
}

function openMobileNav() {
  if (!mobileNavPanel || !mobileNavToggle) return;
  mobileNavPanel.classList.add("is-open");
  mobileNavPanel.setAttribute("aria-hidden", "false");
  mobileNavBackdrop?.classList.add("is-open");
  mobileNavBackdrop?.setAttribute("aria-hidden", "false");
  mobileNavOpen = true;
  mobileNavToggle.setAttribute("aria-expanded", "true");
  document.documentElement.classList.add("med-nav-open");
  document.body.classList.add("med-nav-open");
  updateMobileNavAria();
  mobileNavPanel.querySelector(".med-topnav__mobile-close")?.focus();
}

function isSamePageHashLink(anchor) {
  const href = anchor.getAttribute("href");
  if (!href || !href.includes("#")) return false;
  if (href.startsWith("#")) return true;
  const [pathPart, hashPart] = href.split("#");
  if (!hashPart) return false;
  const path = pathPart || window.location.pathname;
  return path === window.location.pathname;
}

function bindMobileNavLinks() {
  if (!mobileNavPanel) return;

  mobileNavPanel.querySelectorAll("a.med-topnav__mobile-link, a.med-btn").forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const href = anchor.getAttribute("href");
      if (!href || href === "#") return;

      if (isSamePageHashLink(anchor)) {
        closeMobileNav();
        return;
      }

      // Do not hide the drawer before navigation — iOS/Safari can cancel the tap.
      if (href.startsWith("/") || href.startsWith("http")) {
        return;
      }

      closeMobileNav();
    });
  });

  mobileNavPanel.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      closeMobileNav();
    });
  });
}

export function initNavbar() {
  mobileNavToggle = document.querySelector("[data-nav-toggle]");
  mobileNavPanel = document.getElementById("mobile-nav");
  mobileNavBackdrop = document.querySelector(".med-topnav__mobile-backdrop");
  if (!mobileNavToggle || !mobileNavPanel) return;

  mobileNavOpen = mobileNavPanel.classList.contains("is-open");
  mobileNavToggle.setAttribute("aria-expanded", String(mobileNavOpen));
  updateMobileNavAria();

  mobileNavToggle.addEventListener("click", () => {
    if (mobileNavOpen) closeMobileNav();
    else openMobileNav();
  });

  document.querySelectorAll("[data-nav-close]").forEach((el) => {
    el.addEventListener("click", () => closeMobileNav());
  });

  bindMobileNavLinks();

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileNavOpen) closeMobileNav();
  });

  onLanguageChange(updateMobileNavAria);
}
