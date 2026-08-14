"use client";

/**
 * Contexte d'authentification global : utilisateur connecté, connexion, déconnexion.
 * Correctif #12 : la session est portée par des cookies httpOnly posés par le
 * serveur (access token + refresh token) — le frontend ne lit ni ne stocke
 * plus aucun jeton lui-même (jusqu'ici conservé en localStorage, lisible par
 * tout script exécuté sur la page). L'état d'authentification est déterminé
 * en interrogeant /auth/me au chargement : succès = connecté, 401 = non
 * connecté, sans jamais avoir besoin d'inspecter un jeton côté client.
 */
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { authApi } from "@/lib/api";
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
    try {
      const response = await authApi.me();
      setUser(response.data);
    } catch {
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
    setUser(response.data.user);
    return response.data.user as User;
  }, []);

  const logout = useCallback(() => {
    authApi.logout().catch(() => undefined);
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
