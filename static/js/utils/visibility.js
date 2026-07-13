/**
 * Toggle element visibility (hidden attribute + inline display fallback).
 */

export function setVisible(el, visible) {
  if (!el) return;
  el.hidden = !visible;
  el.style.display = visible ? "" : "none";
}

export function isElementVisible(el) {
  if (!el) return { missing: true };
  return {
    hidden: el.hidden,
    display: window.getComputedStyle(el).display,
    inlineDisplay: el.style.display,
  };
}
