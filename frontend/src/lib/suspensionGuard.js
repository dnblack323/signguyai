/**
 * Lightweight client-side helper for handling tenant-suspension responses
 * from the backend. The backend signals suspension by returning HTTP 403
 * with a structured detail of the form:
 *   { code: "tenant_suspended", message, reason, suspended_at }
 *
 * When that happens we stash the info in sessionStorage and route the user
 * to the /account-suspended screen.
 */

import { clearAuthToken } from './authStorage';

const KEY = 'tenant_suspension_info';

export const isTenantSuspendedDetail = (detail) => {
  if (!detail) return false;
  if (typeof detail === 'object' && detail.code === 'tenant_suspended') {
    return true;
  }
  return false;
};

export const saveSuspensionInfo = (detail) => {
  if (!detail) return;
  try {
    sessionStorage.setItem(KEY, JSON.stringify(detail));
  } catch {
    /* ignore */
  }
};

export const getSuspensionInfo = () => {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const clearSuspensionInfo = () => {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
};

/**
 * Hard-redirect to the suspension screen. Clears the auth token so an
 * impersonation-aware app session also resets cleanly. Idempotent — multiple
 * concurrent failures all converge on the same screen.
 */
export const redirectToSuspendedScreen = () => {
  try {
    clearAuthToken();
  } catch {
    /* ignore */
  }
  if (typeof window !== 'undefined' && window.location.pathname !== '/account-suspended') {
    window.location.replace('/account-suspended');
  }
};
