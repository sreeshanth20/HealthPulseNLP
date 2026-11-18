"use client";

import { ROLE_HOME, type Role, type User } from "@/lib/types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "hp_token";
const USER_KEY = "hp_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function storeSession(token: string, user: User) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new CustomEvent("hp_auth_change", { detail: user }));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new CustomEvent("hp_auth_change", { detail: null }));
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (init.body && !(init.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the HealthPulse API. Is the backend running on http://localhost:8000?");
  }

  if (response.status === 204) return undefined as T;
  if (response.status === 401 && typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login")) {
    clearSession();
    window.location.href = "/login?expired=1";
    throw new ApiError(401, "Session expired");
  }
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      (payload && (typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail))) ||
      `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  upload: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export async function login(email: string, password: string): Promise<User> {
  let r: Response;
  try {
    r = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), password }),
    });
  } catch (err) {
    throw new ApiError(0, "Cannot reach the HealthPulse backend server. Please verify backend is running on http://localhost:8000.");
  }

  const payload = await r.json().catch(() => null);
  if (!r.ok) {
    throw new ApiError(r.status, payload?.detail || "Invalid email or password");
  }
  if (!payload?.access_token || !payload?.user) {
    throw new ApiError(500, "Unexpected login response format");
  }
  storeSession(payload.access_token, payload.user);
  return payload.user as User;
}

export function homeForRole(role: Role): string {
  return ROLE_HOME[role] || "/dashboard";
}
