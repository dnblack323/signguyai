/**
 * analytics.js — Lightweight event tracker for SignGuy AI.
 *
 * Tracks: page_view, login_success, login_failed, logout,
 *         account_created, order_created, quote_created,
 *         webstore_created, error, frontend_error, api_error
 *
 * Storage:
 *   visitor_id  → localStorage  (persists across sessions)
 *   session_id  → sessionStorage (resets on tab close)
 */

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// ── ID helpers ────────────────────────────────────────────────────────────────
function genId() {
  return 'xxxx-xxxx-4xxx-yxxx-xxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function getVisitorId() {
  try {
    let vid = localStorage.getItem('sg_vid');
    if (!vid) { vid = genId(); localStorage.setItem('sg_vid', vid); }
    return vid;
  } catch { return genId(); }
}

function getSessionId() {
  try {
    let sid = sessionStorage.getItem('sg_sid');
    if (!sid) { sid = genId(); sessionStorage.setItem('sg_sid', sid); }
    return sid;
  } catch { return genId(); }
}

// ── Core send ─────────────────────────────────────────────────────────────────
export async function trackEvent(eventType, metadata = {}) {
  try {
    const payload = {
      event_type:  eventType,
      session_id:  getSessionId(),
      visitor_id:  getVisitorId(),
      user_id:     metadata.user_id   || null,
      tenant_id:   metadata.tenant_id || null,
      route:       window.location.pathname,
      referrer:    document.referrer || null,
      user_agent:  navigator.userAgent,
      metadata,
    };
    // fire-and-forget (don't await to avoid slowing the app)
    fetch(`${API_URL}/api/analytics/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
  } catch (_) {}
}

// ── Page view tracker (call once per route change) ────────────────────────────
export function trackPageView(route, userContext = {}) {
  trackEvent('page_view', {
    user_id:   userContext.id   || null,
    tenant_id: userContext.tenant_id || null,
    page:      route,
  });
}

// ── Global error capture ──────────────────────────────────────────────────────
let _errorTrackingInitialized = false;

export function initErrorTracking(userContext = {}) {
  // Guard: only attach listeners once to avoid stacking duplicates
  if (_errorTrackingInitialized) return;
  _errorTrackingInitialized = true;

  // JS runtime errors
  window.addEventListener('error', (ev) => {
    trackEvent('frontend_error', {
      user_id:   userContext.id   || null,
      tenant_id: userContext.tenant_id || null,
      message:   ev.message   || 'unknown error',
      filename:  ev.filename  || '',
      lineno:    ev.lineno    || 0,
      colno:     ev.colno     || 0,
    });
  });

  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', (ev) => {
    trackEvent('frontend_error', {
      user_id:   userContext.id   || null,
      tenant_id: userContext.tenant_id || null,
      message:   String(ev.reason?.message || ev.reason || 'unhandled rejection'),
    });
  });
}
