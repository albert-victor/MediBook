/**
 * Map API status / enum values to i18n keys
 */

import { t } from "./translator.js";

const APPOINTMENT_STATUS = {
  pending: "status.appointment.pending",
  scheduled: "status.appointment.scheduled",
  confirmed: "status.appointment.confirmed",
  completed: "status.appointment.completed",
  cancelled: "status.appointment.cancelled",
  no_show: "status.appointment.noShow",
};

const PAYMENT_STATUS = {
  pending: "status.payment.pending",
  processing: "status.payment.processing",
  completed: "status.payment.completed",
  failed: "status.payment.failed",
  refunded: "status.payment.refunded",
};

const PAYMENT_METHOD = {
  mpesa: "status.paymentMethod.mpesa",
  mixx: "status.paymentMethod.mixx",
  airtel_money: "status.paymentMethod.airtel",
  halopesa: "status.paymentMethod.halopesa",
  azampesa: "status.paymentMethod.azampesa",
  selcom_pay: "status.paymentMethod.selcom",
};

const DOCTOR_ACTIVE = {
  true: "status.doctor.active",
  false: "status.doctor.inactive",
};

/**
 * @param {string} status
 * @param {string} [fallbackLabel]
 */
export function appointmentStatus(status, fallbackLabel = "") {
  const key = APPOINTMENT_STATUS[status];
  return key ? t(key) : fallbackLabel || status;
}

/**
 * @param {string} status
 * @param {string} [fallbackLabel]
 */
export function paymentStatus(status, fallbackLabel = "") {
  const key = PAYMENT_STATUS[status];
  return key ? t(key) : fallbackLabel || status;
}

/**
 * @param {string} method
 * @param {string} [fallbackLabel]
 */
export function paymentMethod(method, fallbackLabel = "") {
  const key = PAYMENT_METHOD[method];
  return key ? t(key) : fallbackLabel || method;
}

/**
 * @param {boolean} isActive
 */
export function doctorActiveLabel(isActive) {
  return t(DOCTOR_ACTIVE[String(isActive)]);
}
