/**
 * mediBook Dropdown - toggle menus
 */

function closeAll(except = null) {
  document.querySelectorAll(".med-dropdown.is-open").forEach((el) => {
    if (el !== except) {
      el.classList.remove("is-open");
      el.querySelector("[data-dropdown-trigger]")?.setAttribute("aria-expanded", "false");
    }
  });
}

function initDropdown(dropdown) {
  const trigger = dropdown.querySelector("[data-dropdown-trigger]");
  if (!trigger) return;

  const setExpanded = (open) => {
    trigger.setAttribute("aria-expanded", String(open));
  };

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.contains("is-open");
    closeAll();
    if (!isOpen) {
      dropdown.classList.add("is-open");
      setExpanded(true);
    } else {
      setExpanded(false);
    }
  });

  dropdown.querySelectorAll(".med-dropdown__item").forEach((item) => {
    item.addEventListener("click", () => {
      dropdown.classList.remove("is-open");
      setExpanded(false);
    });
  });
}

export function initDropdowns(root = document) {
  root.querySelectorAll(".med-dropdown").forEach(initDropdown);
}

document.addEventListener("click", () => closeAll());
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAll();
});
