"use client";

import { ShieldCheck } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AdminSidebar } from "@/components/layout/admin-sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuth } from "@/lib/auth-context";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isLoginPage = pathname === "/admin/login";

  useEffect(() => {
    if (isLoginPage || isLoading) return;
    if (!user) {
      router.replace("/admin/login");
      return;
    }
    if (user.role?.name !== "Administrateur") {
      router.replace("/dashboard");
    }
  }, [isLoginPage, isLoading, user, router]);

  if (isLoginPage) return <>{children}</>;

  if (isLoading || !user || user.role?.name !== "Administrateur") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background text-muted-foreground">
        <ShieldCheck className="h-8 w-8 animate-pulse text-primary" />
        <p className="text-sm">Vérification des accès administrateur…</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-muted/20">
      <AdminSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenSidebar={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
