import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { setApiKey, getStoredApiKey } from '../utils/api';

const API_BASE = '/api';

interface AuthState {
  /** null = still loading, true = authenticated, false = not authenticated */
  isAuthenticated: boolean | null;
  /** Whether the backend requires authentication */
  authEnabled: boolean;
  /** True while checking auth status with backend */
  isLoading: boolean;
  /** Error message from last action */
  error: string | null;
  /** Logged-in username (if authenticated) */
  username: string | null;
}

interface AuthContextType extends AuthState {
  /** Attempt to log in with username and password */
  login: (username: string, password: string) => Promise<boolean>;
  /** Register a new account and auto-login */
  register: (username: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  /** Clear session token and log out */
  logout: () => void;
  /** Re-check auth status with the backend */
  checkAuth: () => Promise<void>;
  /** Whether registration is open */
  registrationOpen: boolean;
}

const initialState: AuthState & { registrationOpen: boolean } = {
  isAuthenticated: null,
  authEnabled: false,
  isLoading: true,
  error: null,
  username: null,
  registrationOpen: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState & { registrationOpen: boolean }>(initialState);

  const checkAuth = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await fetch(`${API_BASE}/auth/status`);
      if (!res.ok) {
        setState(prev => ({
          ...prev,
          isAuthenticated: false,
          authEnabled: false,
          isLoading: false,
          error: 'Cannot connect to server. Make sure the backend is running.',
          username: null,
        }));
        return;
      }
      const data = await res.json();

      setState(prev => ({ ...prev, registrationOpen: data.registration_open ?? true }));

      if (!data.auth_enabled) {
        setState(prev => ({
          ...prev,
          isAuthenticated: true,
          authEnabled: false,
          isLoading: false,
          error: null,
          username: null,
        }));
        return;
      }

      // Check if we have a stored session token
      const storedKey = getStoredApiKey();
      if (!storedKey) {
        setState(prev => ({
          ...prev,
          isAuthenticated: false,
          authEnabled: true,
          isLoading: false,
          error: null,
          username: null,
        }));
        return;
      }

      // Verify the stored token against the backend
      try {
        const verifyRes = await fetch(`${API_BASE}/auth/verify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: storedKey }),
        });
        const verifyData = await verifyRes.json();

        if (verifyData.valid) {
          // Token is still valid
          setState(prev => ({
            isAuthenticated: true,
            authEnabled: true,
            isLoading: false,
            error: null,
            username: localStorage.getItem('trinetra_username'),
            registrationOpen: prev.registrationOpen,
          }));          } else {
          // Token expired or server restarted — clear it
          setApiKey(null);
          try { localStorage.removeItem('trinetra_username'); } catch {}
          setState(prev => ({
            ...prev,
            isAuthenticated: false,
            authEnabled: true,
            isLoading: false,
            error: null,
            username: null,
          }));
        }
      } catch {
        // Can't reach server — assume token is valid (optimistic)
        setState(prev => ({
          isAuthenticated: true,
          authEnabled: true,
          isLoading: false,
          error: null,
          username: localStorage.getItem('trinetra_username'),
          registrationOpen: prev.registrationOpen,
        }));
      }
    } catch {
      setState(prev => ({
        ...prev,
        isAuthenticated: false,
        authEnabled: false,
        isLoading: false,
        error: 'Network error. Please check your connection and try again.',
        username: null,
      }));
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await res.json();

      if (data.success && data.token) {
        setApiKey(data.token);
        try {
          localStorage.setItem('trinetra_username', data.username || username);
        } catch {}
        setState(prev => ({
          isAuthenticated: true,
          authEnabled: true,
          isLoading: false,
          error: null,
          username: data.username || username,
          registrationOpen: prev.registrationOpen,
        }));
        return { success: true };
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
        }));
        return { success: false, error: data.error || 'Registration failed.' };
      }
    } catch {
      setState(prev => ({
        ...prev,
        isLoading: false,
      }));
      return { success: false, error: 'Network error. Could not connect to server.' };
    }
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (data.success && data.token) {
        setApiKey(data.token);
        try {
          localStorage.setItem('trinetra_username', data.username || username);
        } catch {}
        setState(prev => ({
          ...prev,
          isAuthenticated: true,
          authEnabled: true,
          isLoading: false,
          error: null,
          username: data.username || username,
        }));
        return true;
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: data.error || 'Invalid username or password.',
          username: null,
        }));
        return false;
      }
    } catch {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Network error. Could not connect to server.',
        username: null,
      }));
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    setApiKey(null);
    try {
      localStorage.removeItem('trinetra_username');
    } catch {}
    setState(prev => ({
      ...prev,
      isAuthenticated: false,
      authEnabled: true,
      isLoading: false,
      error: null,
      username: null,
    }));
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, checkAuth, registrationOpen: state.registrationOpen }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
