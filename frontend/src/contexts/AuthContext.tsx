import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { authApi } from '../services/auth';
import type { AuthUser } from '../services/auth';

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'purpleclaw.auth_token';
const USER_KEY = 'purpleclaw.auth_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const raw = localStorage.getItem(USER_KEY);
      const user = raw ? (JSON.parse(raw) as AuthUser) : null;
      return { user, token, loading: false };
    } catch {
      return { user: null, token: null, loading: false };
    }
  });

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setState({ user: null, token: null, loading: false });
  }, []);

  // Handle 401s dispatched by the axios interceptor (avoids hard page reload)
  useEffect(() => {
    window.addEventListener('purpleclaw:unauthorized', clearAuth);
    return () => window.removeEventListener('purpleclaw:unauthorized', clearAuth);
  }, [clearAuth]);

  // On mount, validate the stored token — only evict on 401, not on 429 or network errors
  useEffect(() => {
    if (!state.token) return;
    authApi.me(state.token).catch((err: unknown) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) clearAuth();
    });
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true }));
    try {
      const result = await authApi.login(username, password);
      localStorage.setItem(TOKEN_KEY, result.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(result.user));
      setState({ user: result.user, token: result.access_token, loading: false });
    } catch (err) {
      setState((prev) => ({ ...prev, loading: false }));
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setState({ user: null, token: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        isAuthenticated: state.user !== null && state.token !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
