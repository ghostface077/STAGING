"use client";

/**
 * Contexte d'authentification global : utilisateur connecté, connexion, déconnexion.
 * Le token JWT est conservé dans le localStorage et injecté automatiquement par lib/api.ts.
 */
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { authApi } from "@/lib/api";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const loadUser = useCallback(async () => {
    const token = typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_STORAGE_KEY) : null;
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const response = await authApi.me();
      setUser(response.data);
    } catch {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, response.data.access_token);
    setUser(response.data.user);
    return response.data.user as User;
  }, []);

  const logout = useCallback(() => {
    authApi.logout().catch(() => undefined);
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setUser(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, isLoading, login, logout, refreshUser: loadUser }),
    [user, isLoading, login, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth doit être utilisé à l'intérieur d'un AuthProvider.");
  }
  return context;
}
