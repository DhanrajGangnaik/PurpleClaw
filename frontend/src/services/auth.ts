import axios from 'axios';

const BASE = '/api/v1';

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const authApi = {
  async login(username: string, password: string): Promise<AuthToken> {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const { data } = await axios.post<AuthToken>(`${BASE}/auth/login`, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },

  async me(token: string): Promise<AuthUser> {
    const { data } = await axios.get<AuthUser>(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};
