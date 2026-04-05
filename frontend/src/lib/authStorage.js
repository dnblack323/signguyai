const AUTH_KEY = 'auth_token';
const PORTAL_KEY = 'portal_token';
const EMPLOYEE_KEY = 'employee_token';
const PORTAL_CUSTOMER_ID_KEY = 'portal_customer_id';
const PORTAL_CUSTOMER_NAME_KEY = 'portal_customer_name';
const EMPLOYEE_ID_KEY = 'employee_id';
const EMPLOYEE_NAME_KEY = 'employee_name';
const EMPLOYEE_TENANT_ID_KEY = 'employee_tenant_id';
const EMPLOYEE_PORTAL_CONFIG_KEY = 'employee_portal_config';

// TODO(auth-migration): Replace browser-stored auth tokens with secure HttpOnly
// cookie-based sessions. These helpers centralize token access so that migration
// can happen in one place instead of throughout the app.

const readSessionValue = (key) => sessionStorage.getItem(key) || null;
const readPersistentValue = (key) => localStorage.getItem(key) || null;
const readSessionFirstValue = (key) => readSessionValue(key) || readPersistentValue(key);

const writeValue = (key, value, persistent = false) => {
  sessionStorage.removeItem(key);
  localStorage.removeItem(key);
  if (!value) return;
  (persistent ? localStorage : sessionStorage).setItem(key, value);
};
const clearValue = (key) => {
  sessionStorage.removeItem(key);
  localStorage.removeItem(key);
};

export const getPersistentPreference = (key, fallbackValue = null) => {
  const value = readPersistentValue(key);
  return value ?? fallbackValue;
};

export const setPersistentPreference = (key, value) => {
  if (value === undefined || value === null) {
    localStorage.removeItem(key);
    return;
  }
  localStorage.setItem(key, value);
};

export const clearPersistentPreference = (key) => {
  localStorage.removeItem(key);
};

export const getAuthToken = () => readSessionFirstValue(AUTH_KEY);
export const setAuthToken = (token, persistent = false) => writeValue(AUTH_KEY, token, persistent);
export const clearAuthToken = () => clearValue(AUTH_KEY);

export const getPortalToken = () => readSessionFirstValue(PORTAL_KEY);
export const setPortalToken = (token, persistent = false) => writeValue(PORTAL_KEY, token, persistent);
export const clearPortalToken = () => clearValue(PORTAL_KEY);

export const getEmployeePortalToken = () => readSessionFirstValue(EMPLOYEE_KEY);
export const setEmployeePortalToken = (token, persistent = false) => writeValue(EMPLOYEE_KEY, token, persistent);
export const clearEmployeePortalToken = () => clearValue(EMPLOYEE_KEY);

export const getPortalCustomerId = () => readSessionValue(PORTAL_CUSTOMER_ID_KEY);
export const setPortalCustomerId = (value) => writeValue(PORTAL_CUSTOMER_ID_KEY, value, false);
export const clearPortalCustomerId = () => clearValue(PORTAL_CUSTOMER_ID_KEY);

export const getPortalCustomerName = () => readSessionValue(PORTAL_CUSTOMER_NAME_KEY);
export const setPortalCustomerName = (value) => writeValue(PORTAL_CUSTOMER_NAME_KEY, value, false);
export const clearPortalCustomerName = () => clearValue(PORTAL_CUSTOMER_NAME_KEY);

export const getEmployeePortalId = () => readSessionValue(EMPLOYEE_ID_KEY);
export const setEmployeePortalId = (value) => writeValue(EMPLOYEE_ID_KEY, value, false);
export const clearEmployeePortalId = () => clearValue(EMPLOYEE_ID_KEY);

export const getEmployeePortalName = () => readSessionValue(EMPLOYEE_NAME_KEY);
export const setEmployeePortalName = (value) => writeValue(EMPLOYEE_NAME_KEY, value, false);
export const clearEmployeePortalName = () => clearValue(EMPLOYEE_NAME_KEY);

export const getEmployeePortalTenantId = () => readSessionValue(EMPLOYEE_TENANT_ID_KEY);
export const setEmployeePortalTenantId = (value) => writeValue(EMPLOYEE_TENANT_ID_KEY, value, false);
export const clearEmployeePortalTenantId = () => clearValue(EMPLOYEE_TENANT_ID_KEY);

export const getEmployeePortalConfig = () => {
  const raw = readSessionValue(EMPLOYEE_PORTAL_CONFIG_KEY);
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
};
export const setEmployeePortalConfig = (value) => writeValue(EMPLOYEE_PORTAL_CONFIG_KEY, JSON.stringify(value || {}), false);
export const clearEmployeePortalConfig = () => clearValue(EMPLOYEE_PORTAL_CONFIG_KEY);