/**
 * Landing page interactions
 */

import { i18nReady } from "../i18n/languageManager.js";
import { initCarousels } from "../utils/carousel.js";

function initScrollSpy() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll('.med-topnav__link[href^="#"]');
  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          navLinks.forEach((link) => {
            link.classList.toggle("is-active", link.getAttribute("href") === `#${id}`);
          });
        }
      });
    },
    { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
  );

  sections.forEach((section) => observer.observe(section));
}

function initSmoothAnchors() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;
      const target = document.querySelector(targetId);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function initServiceIcons() {
  document.querySelectorAll("[data-service-icon]").forEach((icon) => {
    icon.addEventListener("click", () => {
      const circle = icon.querySelector(".landing-service-icon__circle");
      if (!circle) return;

      circle.style.transform = "scale(0.92)";
      requestAnimationFrame(() => {
        setTimeout(() => {
          circle.style.transform = "";
        }, 150);
      });
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await i18nReady;
  initScrollSpy();
  initSmoothAnchors();
  initServiceIcons();
  initCarousels();
});
