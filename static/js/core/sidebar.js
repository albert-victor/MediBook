/**
 * mediBook Sidebar - mobile toggle & collapse
 */

export function initSidebar() {
  const sidebar = document.querySelector(".med-sidebar");
  if (!sidebar) return;

  const backdrop = document.querySelector(".med-sidebar-backdrop");
  const toggleBtns = document.querySelectorAll("[data-sidebar-toggle]");
  const collapseBtn = document.querySelector("[data-sidebar-collapse]");

  const open = () => {
    sidebar.classList.add("is-open");
    backdrop?.classList.add("is-visible");
    document.body.style.overflow = "hidden";
  };

  const close = () => {
    sidebar.classList.remove("is-open");
    backdrop?.classList.remove("is-visible");
    document.body.style.overflow = "";
  };

  toggleBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      sidebar.classList.contains("is-open") ? close() : open();
    });
  });

  backdrop?.addEventListener("click", close);

  collapseBtn?.addEventListener("click", () => {
    sidebar.classList.toggle("med-sidebar--collapsed");
  });
}
