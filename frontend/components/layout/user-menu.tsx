"use client";

import { LayoutDashboard, LogOut, Settings, User as UserIcon } from "lucide-react";
import Link from "next/link";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth-context";
import { getInitials } from "@/lib/utils";

export function UserMenu() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <Avatar>
          <AvatarFallback>{getInitials(user.first_name, user.last_name)}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <p className="text-sm font-medium">
            {user.first_name} {user.last_name}
          </p>
          <p className="text-xs font-normal text-muted-foreground">{user.role?.name}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profil">
            <UserIcon /> Mon profil
          </Link>
        </DropdownMenuItem>
        {user.role?.name === "Administrateur" && (
          <DropdownMenuItem asChild>
            <Link href="/admin/dashboard">
              <Settings /> Back-office administrateur
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuItem asChild>
          <Link href="/dashboard">
            <LayoutDashboard /> Tableau de bord
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => logout()} className="text-destructive focus:text-destructive">
          <LogOut /> Se déconnecter
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
