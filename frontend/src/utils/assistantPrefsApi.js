/**
 * Phase 5 — client wrapper for /api/ai/assistant/prefs/* and related
 * personalization endpoints (saved commands, routines, preferences,
 * smart defaults, next-step suggestions, bulk overdue reminders).
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const authHeaders = (token) => ({
  headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
});

// ---------- Saved commands ----------
export const listSavedCommands = (token) =>
  axios.get(`${API_URL}/api/ai/assistant/saved-commands`, authHeaders(token)).then((r) => r.data);

export const createSavedCommand = (token, payload) =>
  axios.post(`${API_URL}/api/ai/assistant/saved-commands`, payload, authHeaders(token)).then((r) => r.data);

export const updateSavedCommand = (token, id, payload) =>
  axios.put(`${API_URL}/api/ai/assistant/saved-commands/${id}`, payload, authHeaders(token)).then((r) => r.data);

export const deleteSavedCommand = (token, id) =>
  axios.delete(`${API_URL}/api/ai/assistant/saved-commands/${id}`, authHeaders(token)).then((r) => r.data);

export const recordSavedCommandRun = (token, id) =>
  axios.post(`${API_URL}/api/ai/assistant/saved-commands/${id}/record-run`, {}, authHeaders(token)).then((r) => r.data);

// ---------- Routines ----------
export const listRoutines = (token) =>
  axios.get(`${API_URL}/api/ai/assistant/routines`, authHeaders(token)).then((r) => r.data);

export const createRoutine = (token, payload) =>
  axios.post(`${API_URL}/api/ai/assistant/routines`, payload, authHeaders(token)).then((r) => r.data);

export const updateRoutine = (token, id, payload) =>
  axios.put(`${API_URL}/api/ai/assistant/routines/${id}`, payload, authHeaders(token)).then((r) => r.data);

export const deleteRoutine = (token, id) =>
  axios.delete(`${API_URL}/api/ai/assistant/routines/${id}`, authHeaders(token)).then((r) => r.data);

export const recordRoutineRun = (token, id) =>
  axios.post(`${API_URL}/api/ai/assistant/routines/${id}/record-run`, {}, authHeaders(token)).then((r) => r.data);

// ---------- Preferences (Quick / Guided / Power) ----------
export const getPreferences = (token) =>
  axios.get(`${API_URL}/api/ai/assistant/preferences`, authHeaders(token)).then((r) => r.data);

export const updatePreferences = (token, payload) =>
  axios.put(`${API_URL}/api/ai/assistant/preferences`, payload, authHeaders(token)).then((r) => r.data);

// ---------- Smart default ----------
export const getLastOrderCustomer = (token) =>
  axios.get(`${API_URL}/api/ai/assistant/smart-defaults/last-order-customer`, authHeaders(token)).then((r) => r.data);

// ---------- Next-step suggestions ----------
export const getNextStepSuggestions = (token, actionType, result = {}) =>
  axios.post(
    `${API_URL}/api/ai/assistant/next-step-suggestions`,
    { action_type: actionType, result },
    authHeaders(token),
  ).then((r) => r.data);

// ---------- Bulk overdue reminders ----------
export const previewOverdueReminders = (token) =>
  axios.get(`${API_URL}/api/ai/assistant/bulk/overdue-reminders/preview`, authHeaders(token)).then((r) => r.data);

export const sendOverdueReminders = (token, payload = {}) =>
  axios.post(
    `${API_URL}/api/ai/assistant/bulk/overdue-reminders/send`,
    payload,
    authHeaders(token),
  ).then((r) => r.data);
