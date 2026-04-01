const AUTH_KEY = 'auth_token';
const PORTAL_KEY = 'portal_token';
const EMPLOYEE_KEY = 'employee_token';

const readValue = (key) => sessionStorage.getItem(key) || localStorage.getItem(key) || null;
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

export const getAuthToken = () => readValue(AUTH_KEY);
export const setAuthToken = (token, persistent = false) => writeValue(AUTH_KEY, token, persistent);
export const clearAuthToken = () => clearValue(AUTH_KEY);

export const getPortalToken = () => readValue(PORTAL_KEY);
export const setPortalToken = (token, persistent = false) => writeValue(PORTAL_KEY, token, persistent);
export const clearPortalToken = () => clearValue(PORTAL_KEY);

export const getEmployeePortalToken = () => readValue(EMPLOYEE_KEY);
export const setEmployeePortalToken = (token, persistent = false) => writeValue(EMPLOYEE_KEY, token, persistent);
export const clearEmployeePortalToken = () => clearValue(EMPLOYEE_KEY);