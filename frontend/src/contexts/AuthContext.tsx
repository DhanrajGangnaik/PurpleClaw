import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { authApi, setToken } from '../services';
import type { AuthUser } from '../services/auth';

interface AuthState { user: AuthUser | null; token: string | null; loading: boolean; }
interface AuthContextValue extends AuthState {
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const Ctx = createContext<AuthContextValue | null>(null);
const TK = 'purpleclaw.token';
const UK = 'purpleclaw.user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    try {
      const token = localStorage.getItem(TK);
      const user = JSON.parse(localStorage.getItem(UK) ?? 'null') as AuthUser | null;
      if (token) setToken(token);
      return { user, token, loading: false };
    } catch { return { user: null, token: null, loading: false }; }
  });

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TK); localStorage.removeItem(UK);
    setToken(null);
    setState({ user: null, token: null, loading: false });
  }, []);

  useEffect(() => {
    window.addEventListener('purpleclaw:unauthorized', clearAuth);
    return () => window.removeEventListener('purpleclaw:unauthorized', clearAuth);
  }, [clearAuth]);

  const login = useCallback(async (username: string, password: string) => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const result = await authApi.login(username, password);
      localStorage.setItem(TK, result.access_token);
      localStorage.setItem(UK, JSON.stringify(result.user));
      setToken(result.access_token);
      setState({ user: result.user, token: result.access_token, loading: false });
    } catch (e) { setState((s) => ({ ...s, loading: false })); throw e; }
  }, []);

  const logout = useCallback(() => { clearAuth(); }, [clearAuth]);

  return (
    <Ctx.Provider value={{ ...state, isAuthenticated: !!state.token, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
