import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current user profile using token
  const fetchUserProfile = useCallback(async (authToken) => {
    try {
      const response = await fetch(`${API_URL}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return userData;
      } else {
        // Token is invalid or expired
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
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

      // Clone response to avoid body stream already read issues
      const responseClone = response.clone();
      
      let data;
      try {
        data = await responseClone.json();
      } catch (parseError) {
        console.error('Error parsing response:', parseError);
        // Try reading from original response as fallback
        try {
          const text = await response.text();
          data = JSON.parse(text);
        } catch (fallbackError) {
          const errorMsg = 'Server error. Please try again.';
          setError(errorMsg);
          return { success: false, error: errorMsg };
        }
      }

      if (response.ok) {
        localStorage.setItem('auth_token', data.access_token);
        setToken(data.access_token);
        await fetchUserProfile(data.access_token);
        return { success: true };
      } else {
        const errorMsg = data.detail || 'Registration failed';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (err) {
      console.error('Registration error:', err);
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Login user
  const login = async (email, password) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      // Clone response to avoid body stream already read issues
      const responseClone = response.clone();
      
      let data;
      try {
        data = await responseClone.json();
      } catch (parseError) {
        console.error('Error parsing response:', parseError);
        // Try reading from original response as fallback
        try {
          const text = await response.text();
          data = JSON.parse(text);
        } catch (fallbackError) {
          const errorMsg = 'Server error. Please try again.';
          setError(errorMsg);
          return { success: false, error: errorMsg };
        }
      }

      if (response.ok) {
        localStorage.setItem('auth_token', data.access_token);
        setToken(data.access_token);
        await fetchUserProfile(data.access_token);
        return { success: true };
      } else {
        const errorMsg = data.detail || 'Invalid email or password';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (err) {
      console.error('Login error:', err);
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Logout user
  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    setError(null);
  };

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
    isLoading,
    error,
    isAuthenticated: !!user,
    register,
    login,
    logout,
    updateProfile,
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
