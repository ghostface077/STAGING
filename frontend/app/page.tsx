"use client";

/** Page d'accueil : redirige vers le tableau de bord si connecté, sinon vers la connexion. */
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LifeBuoy } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    router.replace(user ? "/dashboard" : "/login");
  }, [isLoading, user, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background text-muted-foreground">
      <LifeBuoy className="h-8 w-8 animate-pulse text-primary" />
      <p className="text-sm">Chargement de l’application IT Support…</p>
    </div>
  );
}
