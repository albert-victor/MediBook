/**
 * mediBook Modal - accessible dialog system
 */

let activeModal = null;
let previousFocus = null;

function createBackdrop(modalEl) {
  const backdrop = document.createElement("div");
  backdrop.className = "med-modal-backdrop";
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");

  const title = modalEl.querySelector(".med-modal__title");
  if (title) backdrop.setAttribute("aria-labelledby", title.id || "modal-title");

  backdrop.appendChild(modalEl);
  return backdrop;
}

function trapFocus(backdrop) {
  const focusable = backdrop.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  backdrop.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}

/**
 * Open a modal element or create one from options.
 * @param {HTMLElement|Object} target - modal element or config
 */
export function openModal(target) {
  if (activeModal) closeModal();

  let backdrop;
  let modalEl;

  if (target instanceof HTMLElement) {
    modalEl = target;
    backdrop = createBackdrop(modalEl);
  } else {
    const { title, body, footer, size = "", confirm = false, type = "" } = target;
    modalEl = document.createElement("div");
    modalEl.className = `med-modal ${size ? `med-modal--${size}` : ""} ${confirm ? "med-modal--confirm" : ""}`;

    modalEl.innerHTML = `
      <div class="med-modal__header">
        <div>
          ${confirm ? `<div class="med-modal__icon med-modal__icon--${type}"><i class="bi bi-exclamation-triangle-fill"></i></div>` : ""}
          <h2 class="med-modal__title" id="modal-title">${title}</h2>
        </div>
        <button class="med-modal__close" aria-label="Close"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="med-modal__body">${body || ""}</div>
      ${footer ? `<div class="med-modal__footer">${footer}</div>` : ""}
    `;

    backdrop = createBackdrop(modalEl);
  }

  previousFocus = document.activeElement;
  document.body.appendChild(backdrop);
  document.body.style.overflow = "hidden";

  requestAnimationFrame(() => backdrop.classList.add("is-open"));

  const closeBtn = backdrop.querySelector(".med-modal__close");
  if (closeBtn) closeBtn.addEventListener("click", () => closeModal());

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  trapFocus(backdrop);
  activeModal = backdrop;

  const focusTarget = backdrop.querySelector(".med-modal__close") || backdrop;
  focusTarget.focus();

  return backdrop;
}

export function closeModal() {
  if (!activeModal) return;

  activeModal.classList.remove("is-open");
  activeModal.addEventListener("transitionend", () => {
    activeModal.remove();
    activeModal = null;
    document.body.style.overflow = "";
    previousFocus?.focus();
  }, { once: true });

  setTimeout(() => {
    if (activeModal) {
      activeModal.remove();
      activeModal = null;
      document.body.style.overflow = "";
      previousFocus?.focus();
    }
  }, 400);
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && activeModal) closeModal();
});
