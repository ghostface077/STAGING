"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { notificationsApi } from "@/lib/api";
import { NOTIFICATION_TYPE_LABELS } from "@/lib/constants";
import { formatRelativeTime } from "@/lib/utils";

export function NotificationBell() {
  const queryClient = useQueryClient();

  const { data: countData } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationsApi.unreadCount().then((res) => res.data),
    refetchInterval: 30_000,
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: () => notificationsApi.list().then((res) => res.data.slice(0, 8)),
    refetchInterval: 30_000,
  });

  const unread = countData?.unread ?? 0;

  const handleMarkAllRead = async () => {
    await notificationsApi.markAllAsRead();
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell />
          {unread > 0 && (
            <Badge variant="destructive" className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full px-1 text-[10px]">
              {unread > 9 ? "9+" : unread}
            </Badge>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-sm font-semibold">Notifications</p>
          {unread > 0 && (
            <Button variant="ghost" size="sm" onClick={handleMarkAllRead} className="h-7 px-2 text-xs">
              <CheckCheck className="h-3.5 w-3.5" /> Tout marquer lu
            </Button>
          )}
        </div>
        <Separator />
        <div className="max-h-80 overflow-y-auto scrollbar-thin">
          {!notifications || notifications.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-muted-foreground">Aucune notification pour le moment.</p>
          ) : (
            notifications.map((notification) => (
              <Link
                key={notification.id}
                href={notification.ticket_id ? `/tickets/${notification.ticket_id}` : "/notifications"}
                className={`block border-b border-border px-4 py-3 text-sm transition-colors last:border-0 hover:bg-accent ${
                  notification.is_read ? "" : "bg-primary/5"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium">{notification.title}</p>
                  {!notification.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />}
                </div>
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{notification.message}</p>
                <p className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                  {NOTIFICATION_TYPE_LABELS[notification.type] ?? notification.type} · {formatRelativeTime(notification.created_at)}
                </p>
              </Link>
            ))
          )}
        </div>
        <Separator />
        <Link href="/notifications" className="block px-4 py-3 text-center text-sm font-medium text-primary hover:underline">
          Voir toutes les notifications
        </Link>
      </PopoverContent>
    </Popover>
  );
}
