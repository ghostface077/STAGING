"use client";

import { LayoutDashboard, ShieldCheck, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ADMIN_NAV_GROUPS } from "@/lib/admin-nav-config";
import { cn } from "@/lib/utils";

interface AdminSidebarProps {
  open: boolean;
  onClose: () => void;
}

export function AdminSidebar({ open, onClose }: AdminSidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-800 bg-slate-950 text-slate-200 transition-transform lg:sticky lg:top-0 lg:z-0 lg:h-screen lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between px-4">
          <Link href="/admin/dashboard" className="flex items-center gap-2.5 font-semibold text-white">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <span className="flex flex-col leading-none">
              <span className="text-sm font-semibold">Back-office</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Administration</span>
            </span>
          </Link>
          <Button variant="ghost" size="icon" className="text-slate-300 hover:text-white lg:hidden" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-3 scrollbar-thin">
          {ADMIN_NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{group.label}</p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={cn(
                        "relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        isActive ? "bg-primary text-primary-foreground shadow-sm" : "text-slate-300 hover:bg-slate-800 hover:text-white",
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <Link href="/dashboard" className="flex items-center gap-2 border-t border-slate-800 px-4 py-3 text-xs text-slate-400 hover:text-white">
          <LayoutDashboard className="h-3.5 w-3.5" /> Retour au portail
        </Link>
      </aside>
    </>
  );
}
