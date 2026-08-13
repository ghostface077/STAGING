"use client";

import { LifeBuoy, PlusCircle, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { getPortalNavGroupsForRole } from "@/lib/nav-config";
import { cn, getInitials } from "@/lib/utils";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const { user } = useAuth();
  const pathname = usePathname();
  const groups = getPortalNavGroupsForRole(user?.role?.name);

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-foreground/40 backdrop-blur-[1px] lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card transition-transform lg:sticky lg:top-0 lg:z-0 lg:h-screen lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between px-4">
          <Link href="/dashboard" className="flex items-center gap-2.5 font-semibold">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <LifeBuoy className="h-4 w-4" />
            </span>
            <span className="flex flex-col leading-none">
              <span className="text-sm font-semibold">IT Support</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Service informatique</span>
            </span>
          </Link>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Seul le rôle Utilisateur crée des tickets : un technicien/responsable/administrateur traite ou supervise des tickets déjà existants. */}
        {user?.role?.name === "Utilisateur" && (
          <div className="px-3 pb-2">
            <Button asChild className="w-full justify-start gap-2 shadow-sm">
              <Link href="/tickets/nouveau">
                <PlusCircle className="h-4 w-4" /> Nouveau ticket
              </Link>
            </Button>
          </div>
        )}

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-3 scrollbar-thin">
          {groups.map((group) => (
            <div key={group.label}>
              <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/80">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href + "/"));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                      )}
                    >
                      <span
                        className={cn(
                          "absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-primary transition-opacity",
                          isActive ? "opacity-100" : "opacity-0",
                        )}
                      />
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {user && (
          <Link
            href="/profil"
            className="flex items-center gap-2.5 border-t border-border p-3 text-sm transition-colors hover:bg-accent"
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">{getInitials(user.first_name, user.last_name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium leading-tight">{user.first_name} {user.last_name}</p>
              <p className="truncate text-xs text-muted-foreground">{user.role?.name}</p>
            </div>
          </Link>
        )}
      </aside>
    </>
  );
}
