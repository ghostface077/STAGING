"use client";

import { Menu, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { NotificationBell } from "@/components/layout/notification-bell";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserMenu } from "@/components/layout/user-menu";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface TopbarProps {
  onOpenSidebar: () => void;
}

export function Topbar({ onOpenSidebar }: TopbarProps) {
  const [search, setSearch] = useState("");
  const router = useRouter();

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    if (search.trim()) router.push(`/tickets?search=${encodeURIComponent(search.trim())}`);
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-md sm:px-6">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenSidebar}>
        <Menu className="h-5 w-5" />
      </Button>

      <form onSubmit={handleSearch} className="hidden flex-1 max-w-md items-center gap-2 sm:flex">
        <div className="relative w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Rechercher un ticket, une référence…"
            className="rounded-full bg-muted/60 pl-9 focus-visible:bg-background"
          />
        </div>
      </form>

      <div className="ml-auto flex items-center gap-1">
        <ThemeToggle />
        <NotificationBell />
        <Separator orientation="vertical" className="mx-1 h-6" />
        <UserMenu />
      </div>
    </header>
  );
}
