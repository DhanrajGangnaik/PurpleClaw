import axios from 'axios';

const BASE = '/api';

export interface AuthUser {
  user_id: string;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface UserCreateRequest {
  username: string;
  email?: string;
  password: string;
  role: AuthUser['role'];
}

export interface UserUpdateRequest {
  email?: string;
  role?: AuthUser['role'];
  is_active?: boolean;
  password?: string;
}

export const authApi = {
  async login(username: string, password: string): Promise<AuthToken> {
    const { data } = await axios.post<AuthToken>(`${BASE}/auth/login`, { username, password });
    return data;
  },

  async me(token: string): Promise<AuthUser> {
    const { data } = await axios.get<AuthUser>(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  async listUsers(token: string): Promise<AuthUser[]> {
    const { data } = await axios.get<AuthUser[]>(`${BASE}/auth/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  async createUser(token: string, payload: UserCreateRequest): Promise<AuthUser> {
    const { data } = await axios.post<AuthUser>(`${BASE}/auth/users`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  async updateUser(token: string, userId: string, payload: UserUpdateRequest): Promise<AuthUser> {
    const { data } = await axios.patch<AuthUser>(`${BASE}/auth/users/${userId}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  async deleteUser(token: string, userId: string): Promise<void> {
    await axios.delete(`${BASE}/auth/users/${userId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};
