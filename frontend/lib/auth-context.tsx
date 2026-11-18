"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, clearSession, getStoredUser, getToken, login as apiLogin } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  refresh: () => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => { throw new Error("AuthProvider not mounted"); },
  refresh: async () => {},
  logout: () => {},
  setUser: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("hp_user", JSON.stringify(me));
      }
    } catch {
      // A local profile is display cache only, never proof of authentication.
      // Keeping it active after a failed verification would allow protected UI
      // to render without a validated JWT or a reachable authorization service.
      clearSession();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<User> => {
    setLoading(true);
    try {
      const loggedInUser = await apiLogin(email, password);
      setUser(loggedInUser);
      return loggedInUser;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, []);

  useEffect(() => {
    refresh();

    const handleAuthChange = (e: Event) => {
      const customEvent = e as CustomEvent<User | null>;
      if (customEvent && customEvent.detail !== undefined) {
        setUser(customEvent.detail);
      } else {
        // Browser storage events can be caused by another tab.  A copied
        // profile alone is never enough to restore an authenticated state.
        setUser(getToken() ? getStoredUser() : null);
      }
    };

    window.addEventListener("hp_auth_change", handleAuthChange);
    window.addEventListener("storage", handleAuthChange);
    return () => {
      window.removeEventListener("hp_auth_change", handleAuthChange);
      window.removeEventListener("storage", handleAuthChange);
    };
  }, [refresh]);

  const value = useMemo(
    () => ({ user, loading, login, refresh, logout, setUser }),
    [user, loading, login, refresh, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}
