/**
 * Scroll reveal using Intersection Observer.
 * Sections animate once when entering the viewport.
 */

const REVEAL_SELECTOR = "[data-reveal]";
const STAGGER_SELECTOR = "[data-reveal-stagger]";
const observed = new WeakSet();

function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  return rect.top < window.innerHeight * 0.92 && rect.bottom > 0;
}

function revealElement(el, observer) {
  if (el.classList.contains("is-visible")) return;
  el.classList.add("is-visible");
  observer?.unobserve(el);
}

/**
 * Initialize scroll reveal animations.
 * @param {ParentNode} [root=document] - scope to a subtree (for dynamic content)
 */
export function initScrollReveal(root = document) {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReducedMotion) {
    root.querySelectorAll(`${REVEAL_SELECTOR}, ${STAGGER_SELECTOR} [data-reveal-item]`).forEach((el) => {
      el.classList.add("is-visible");
    });
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          revealElement(entry.target, observer);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -24px 0px" }
  );

  root.querySelectorAll(REVEAL_SELECTOR).forEach((el) => {
    if (observed.has(el)) return;
    observed.add(el);
    el.classList.add("reveal");
    if (isInViewport(el)) {
      revealElement(el, observer);
    } else {
      observer.observe(el);
    }
  });

  root.querySelectorAll(STAGGER_SELECTOR).forEach((container) => {
    container.querySelectorAll("[data-reveal-item]").forEach((item, index) => {
      if (observed.has(item)) return;
      observed.add(item);
      item.classList.add("reveal");
      item.style.transitionDelay = `${Math.min(index, 8) * 60}ms`;
      if (isInViewport(item)) {
        revealElement(item, observer);
      } else {
        observer.observe(item);
      }
    });
  });
}

/**
 * Reveal items inside dynamically replaced content.
 */
export function revealDynamicItems(container) {
  if (!container) return;
  initScrollReveal(container);
}
