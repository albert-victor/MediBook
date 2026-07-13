/**
 * mediBook Design System - Application bootstrap
 */

import { initScrollReveal } from "../utils/scroll-reveal.js";
import { initDropdowns } from "./dropdown.js";
import { initSidebar } from "./sidebar.js";
import { initNavbar } from "./navbar.js";
import "../i18n/languageManager.js";

document.addEventListener("DOMContentLoaded", () => {
  initScrollReveal();
  initDropdowns();
  initSidebar();
  initNavbar();
});

export { toast } from "./toast.js";
export { openModal, closeModal } from "./modal.js";
