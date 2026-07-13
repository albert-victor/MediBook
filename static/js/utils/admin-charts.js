/**
 * Animated SVG pie charts and vertical bar charts for admin reports.
 */

const PIE_COLORS = [
  "#1a6fb5",
  "#0d9488",
  "#38a06a",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
];

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function polar(cx, cy, r, angle) {
  return {
    x: cx + r * Math.cos(angle),
    y: cy + r * Math.sin(angle),
  };
}

function slicePath(cx, cy, r, start, end) {
  if (end - start >= Math.PI * 2 - 0.0001) {
    return `M ${cx} ${cy} m -${r} 0 a ${r} ${r} 0 1 1 ${r * 2} 0 a ${r} ${r} 0 1 1 -${r * 2} 0`;
  }
  const p1 = polar(cx, cy, r, start);
  const p2 = polar(cx, cy, r, end);
  const large = end - start > Math.PI ? 1 : 0;
  return `M ${cx} ${cy} L ${p1.x} ${p1.y} A ${r} ${r} 0 ${large} 1 ${p2.x} ${p2.y} Z`;
}

/**
 * @param {HTMLElement} container
 * @param {Array<{label: string, value: number, display?: string}>} items
 * @param {{ emptyTitle?: string, emptyMessage?: string, centerLabel?: string }} [opts]
 */
export function renderPieChart(container, items, opts = {}) {
  if (!container) return;

  const valid = (items || []).filter((i) => Number(i.value) > 0);
  const total = valid.reduce((sum, i) => sum + Number(i.value), 0);

  if (!total) {
    container.innerHTML = `
      <div class="adash-chart-empty">
        <i class="bi bi-pie-chart"></i>
        <p>${escapeHtml(opts.emptyMessage || "No data")}</p>
      </div>`;
    return;
  }

  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 10;
  let angle = -Math.PI / 2;

  const slices = valid.map((item, index) => {
    const sweep = (Number(item.value) / total) * Math.PI * 2;
    const end = angle + sweep;
    const path = slicePath(cx, cy, r, angle, end);
    const color = PIE_COLORS[index % PIE_COLORS.length];
    const pct = Math.round((Number(item.value) / total) * 100);
    angle = end;
    return { item, path, color, pct, index };
  });

  container.innerHTML = `
    <div class="adash-pie-chart">
      <div class="adash-pie-chart__visual">
        <svg class="adash-pie-chart__svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" role="img" aria-hidden="true">
          ${slices.map((s) => `
            <path
              class="adash-pie-chart__slice"
              d="${s.path}"
              fill="${s.color}"
              style="--slice-i:${s.index}"
            ></path>
          `).join("")}
        </svg>
        <div class="adash-pie-chart__center">
          <strong>${Math.round(total)}</strong>
          <span>${escapeHtml(opts.centerLabel || "Total")}</span>
        </div>
      </div>
      <ul class="adash-pie-chart__legend">
        ${slices.map((s) => `
          <li class="adash-pie-chart__legend-item" style="--legend-color:${s.color}; --legend-i:${s.index}">
            <span class="adash-pie-chart__swatch"></span>
            <span class="adash-pie-chart__legend-label">${escapeHtml(s.item.label)}</span>
            <span class="adash-pie-chart__legend-value">${escapeHtml(s.item.display ?? String(s.item.value))} · ${s.pct}%</span>
          </li>
        `).join("")}
      </ul>
    </div>`;
}

/**
 * @param {HTMLElement} container
 * @param {Array<{label: string, value: number, display?: string}>} items
 * @param {{ color?: string, emptyMessage?: string }} [opts]
 */
export function renderVerticalBarChart(container, items, opts = {}) {
  if (!container) return;

  const valid = (items || []).filter((i) => Number(i.value) >= 0);
  if (!valid.length) {
    container.innerHTML = `
      <div class="adash-chart-empty">
        <i class="bi bi-bar-chart"></i>
        <p>${escapeHtml(opts.emptyMessage || "No data")}</p>
      </div>`;
    return;
  }

  const max = Math.max(...valid.map((i) => Number(i.value)), 1);
  const color = opts.color || "primary";

  container.innerHTML = `
    <div class="adash-vbar-chart">
      ${valid.map((item, index) => {
        const pct = Math.round((Number(item.value) / max) * 100);
        return `
          <div class="adash-vbar-chart__item" style="--bar-i:${index}">
            <div class="adash-vbar-chart__track" aria-hidden="true">
              <div class="adash-vbar-chart__fill adash-vbar-chart__fill--${color}" style="--bar-pct:${pct}%"></div>
            </div>
            <span class="adash-vbar-chart__value">${escapeHtml(item.display ?? String(item.value))}</span>
            <span class="adash-vbar-chart__label">${escapeHtml(item.label)}</span>
          </div>`;
      }).join("")}
    </div>`;
}

/**
 * @param {HTMLElement} container
 * @param {Array<{label: string, value: number, display?: string}>} items
 * @param {{ color?: string, emptyMessage?: string }} [opts]
 */
export function renderHorizontalBarChart(container, items, opts = {}) {
  if (!container) return;

  const valid = (items || []).filter((i) => Number(i.value) >= 0);
  if (!valid.length) {
    container.innerHTML = `
      <div class="adash-chart-empty">
        <i class="bi bi-bar-chart"></i>
        <p>${escapeHtml(opts.emptyMessage || "No data")}</p>
      </div>`;
    return;
  }

  const max = Math.max(...valid.map((i) => Number(i.value)), 1);
  const color = opts.color || "teal";

  container.innerHTML = valid.map((item, index) => {
    const pct = Math.round((Number(item.value) / max) * 100);
    return `
      <div class="adash-bar adash-bar--h" style="--bar-i:${index}">
        <span class="adash-bar__label">${escapeHtml(item.label)}</span>
        <div class="adash-bar__track">
          <div class="adash-bar__fill adash-bar__fill--${color}" style="--bar-pct:${pct}%"></div>
        </div>
        <span class="adash-bar__value">${escapeHtml(item.display ?? String(item.value))}</span>
      </div>`;
  }).join("");
}

/**
 * Convert doctor distribution bar items to pie slices.
 * @param {Array<{label: string, value: number, display?: string}>} items
 */
export function distributionToPieItems(items) {
  return (items || []).map((item) => ({
    label: item.label,
    value: Number(item.value),
    display: item.display ?? String(item.value),
  }));
}
