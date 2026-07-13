/**
 * HTTP client wrapper around Fetch API.
 */

import { tApiMessage } from "../i18n/translator.js";

const API_BASE = "/api/v1";

/**
 * @param {string} endpoint
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
export async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith("/") ? `${API_BASE}${endpoint}` : `${API_BASE}/${endpoint}`;

  const config = {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = error.detail
      ? (typeof error.detail === "string" ? tApiMessage(error.detail) : tApiMessage("Request failed"))
      : `HTTP ${response.status}`;
    throw new Error(detail || tApiMessage("Request failed"));
  }

  if (response.status === 204) return null;
  return response.json();
}
