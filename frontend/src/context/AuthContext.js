import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getAuthToken, setAuthToken, clearAuthToken } from '../lib/authStorage';
import {
  isTenantSuspendedDetail,
  saveSuspensionInfo,
  redirectToSuspendedScreen,
} from '../lib/suspensionGuard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AuthContext = createContext(null);

// Role definitions matching backend
export const UserRole = {
  OWNER: 'owner',
  ADMIN: 'admin',
  STAFF: 'staff',
};

// Permission definitions matching backend
export const Permission = {
  // Customer permissions
  CUSTOMERS_VIEW: 'customers:view',
  CUSTOMERS_CREATE: 'customers:create',
  CUSTOMERS_EDIT: 'customers:edit',
  CUSTOMERS_DELETE: 'customers:delete',
  
  // Quote permissions
  QUOTES_VIEW: 'quotes:view',
  QUOTES_CREATE: 'quotes:create',
  QUOTES_EDIT: 'quotes:edit',
  QUOTES_DELETE: 'quotes:delete',
  QUOTES_CONVERT: 'quotes:convert',
  
  // Job permissions
  JOBS_VIEW: 'jobs:view',
  JOBS_CREATE: 'jobs:create',
  JOBS_EDIT: 'jobs:edit',
  JOBS_DELETE: 'jobs:delete',
  
  // Invoice permissions
  INVOICES_VIEW: 'invoices:view',
  INVOICES_CREATE: 'invoices:create',
  INVOICES_EDIT: 'invoices:edit',
  INVOICES_DELETE: 'invoices:delete',
  
  // Time Clock permissions
  TIMECLOCK_VIEW_OWN: 'timeclock:view_own',
  TIMECLOCK_VIEW_ALL: 'timeclock:view_all',
  TIMECLOCK_CLOCK_IN: 'timeclock:clock_in',
  TIMECLOCK_EDIT: 'timeclock:edit',
  
  // Payroll permissions
  PAYROLL_VIEW: 'payroll:view',
  PAYROLL_EDIT: 'payroll:edit',
  
  // Financial permissions
  FINANCIALS_VIEW: 'financials:view',
  FINANCIALS_CREATE: 'financials:create',
  FINANCIALS_EDIT: 'financials:edit',
  FINANCIALS_DELETE: 'financials:delete',
  
  // User management permissions
  USERS_VIEW: 'users:view',
  USERS_CREATE: 'users:create',
  USERS_EDIT: 'users:edit',
  USERS_DELETE: 'users:delete',
  USERS_MANAGE_ROLES: 'users:manage_roles',
  
  // Webstore permissions
  WEBSTORES_VIEW: 'webstores:view',
  WEBSTORES_CREATE: 'webstores:create',
  WEBSTORES_EDIT: 'webstores:edit',
  WEBSTORES_DELETE: 'webstores:delete',
  
  // AI Tools permissions
  AI_TOOLS_USE: 'ai_tools:use',
  
  // Settings permissions
  SETTINGS_VIEW: 'settings:view',
  SETTINGS_EDIT: 'settings:edit',

  // Inventory and purchasing permissions
  INVENTORY_VIEW: 'inventory:view',
  INVENTORY_PULL: 'inventory:pull',
  INVENTORY_ADJUST: 'inventory:adjust',
  PURCHASING_MANAGE: 'purchasing:manage',
  PURCHASING_APPROVE: 'purchasing:approve',
  VENDORS_MANAGE: 'vendors:manage',
};

const PERMISSION_ALIASES = {
  'timeclock:view_own': ['time:own'],
  'timeclock:view_all': ['time:view_all'],
  'timeclock:clock_in': ['time:own', 'time:manage'],
  'timeclock:edit': ['time:manage'],
  'payroll:edit': ['payroll:manage'],
  'financials:create': ['financials:manage'],
  'financials:edit': ['financials:manage'],
  'financials:delete': ['financials:manage'],
  'settings:edit': ['settings:manage'],
  'users:create': ['users:manage'],
  'users:edit': ['users:manage'],
  'users:delete': ['users:manage'],
  'users:manage_roles': ['users:manage'],
  'webstores:edit': ['webstores:manage'],
  'webstores:delete': ['webstores:manage'],
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [token, setToken] = useState(() => getAuthToken());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current user profile and permissions using token
  const fetchUserProfile = useCallback(async (authToken) => {
    try {
      // Fetch user profile
      const profileResponse = await fetch(`${API_URL}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (profileResponse.ok) {
        const userData = await profileResponse.json();
        setUser(userData);
        
        // Fetch permissions
        const permResponse = await fetch(`${API_URL}/api/users/me/permissions`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (permResponse.ok) {
          const permData = await permResponse.json();
          setPermissions(permData.permissions || []);
        }
        
        return userData;
      } else {
        // If suspended, route to suspension screen instead of just clearing
        if (profileResponse.status === 403) {
          try {
            const data = await profileResponse.json();
            if (isTenantSuspendedDetail(data?.detail)) {
              saveSuspensionInfo(data.detail);
              redirectToSuspendedScreen();
              return null;
            }
          } catch { /* ignore */ }
        }
        // Token is invalid or expired
        clearAuthToken();
        setToken(null);
        setUser(null);
        setPermissions([]);
        return null;
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
      return null;
    }
  }, []);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        await fetchUserProfile(token);
      }
      setIsLoading(false);
    };
    initAuth();
  }, [token, fetchUserProfile]);

  // Register new user
  const register = async (email, password, fullName, companyName) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          company_name: companyName || null,
        }),
      });

      if (!response.ok) {
        let errorMsg = 'Registration failed';
        try {
          const data = await response.json();
          errorMsg = data.detail || errorMsg;
        } catch {
          errorMsg = `Server error (${response.status}). Please try again.`;
        }
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }

      const data = await response.json();
      setAuthToken(data.access_token, true);
      setToken(data.access_token);
      await fetchUserProfile(data.access_token);
      return { success: true };
    } catch (err) {
      console.error('Registration error:', err);
      const errorMsg = 'Network error. Please check your connection and try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Login user
  const login = async (email, password, rememberMe = false) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
      });

      if (!response.ok) {
        let errorMsg = 'Login failed';
        try {
          const data = await response.json();

          // Handle structured tenant-suspended response
          if (response.status === 403 && isTenantSuspendedDetail(data.detail)) {
            saveSuspensionInfo(data.detail);
            redirectToSuspendedScreen();
            return { success: false, error: data.detail.message || 'Account suspended' };
          }

          // detail can be a string or a dict; normalize for display
          if (data.detail) {
            errorMsg = typeof data.detail === 'string'
              ? data.detail
              : (data.detail.message || JSON.stringify(data.detail));
          }
        } catch {
          if (response.status === 401) {
            errorMsg = 'Invalid email or password';
          } else if (response.status === 400) {
            errorMsg = 'Account is disabled';
          } else {
            errorMsg = `Server error (${response.status}). Please try again.`;
          }
        }
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }

      const data = await response.json();
      setAuthToken(data.access_token, rememberMe);
      setToken(data.access_token);
      await fetchUserProfile(data.access_token);
      return { success: true };
    } catch (err) {
      console.error('Login error:', err);
      const errorMsg = 'Network error. Please check your connection and try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Logout user
  const logout = () => {
    clearAuthToken();
    setToken(null);
    setUser(null);
    setPermissions([]);
    setError(null);
  };

  // Check if user has a specific permission
  const hasPermission = (permission) => {
    // Owner, platform_creator, and platform_admin have all permissions
    if (user?.role === UserRole.OWNER || user?.role === 'owner') return true;
    if (user?.role === 'platform_creator' || user?.role === 'platform_admin') return true;
    if (permissions.includes(permission)) return true;
    const aliases = PERMISSION_ALIASES[permission] || [];
    return aliases.some((alias) => permissions.includes(alias));
  };

  // Check if user has any of the specified permissions
  const hasAnyPermission = (...perms) => {
    return perms.some(p => permissions.includes(p));
  };

  // Check if user has all of the specified permissions
  const hasAllPermissions = (...perms) => {
    return perms.every(p => permissions.includes(p));
  };

  // Check if user is owner
  const isOwner = () => user?.role === UserRole.OWNER;
  
  // Check if user is admin or owner
  const isAdminOrOwner = () => user?.role === UserRole.OWNER || user?.role === UserRole.ADMIN;

  // Update user profile
  const updateProfile = async (updates) => {
    if (!token) return { success: false, error: 'Not authenticated' };

    try {
      const params = new URLSearchParams();
      if (updates.full_name) params.append('full_name', updates.full_name);
      if (updates.company_name) params.append('company_name', updates.company_name);

      const response = await fetch(`${API_URL}/api/users/me?${params.toString()}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUser(updatedUser);
        return { success: true, user: updatedUser };
      } else {
        const data = await response.json();
        return { success: false, error: data.detail || 'Update failed' };
      }
    } catch (err) {
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const value = {
    user,
    token,
    permissions,
    isLoading,
    error,
    isAuthenticated: !!user,
    register,
    login,
    logout,
    updateProfile,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isOwner,
    isAdminOrOwner,
    clearError: () => setError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
