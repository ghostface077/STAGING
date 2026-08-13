"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { notificationsApi } from "@/lib/api";
import { NOTIFICATION_TYPE_LABELS } from "@/lib/constants";
import { formatDateTime } from "@/lib/utils";

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"toutes" | "non-lues">("toutes");

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications", "all", filter],
    queryFn: () => notificationsApi.list(filter === "non-lues").then((res) => res.data),
  });

  const handleMarkAsRead = async (id: number) => {
    await notificationsApi.markAsRead(id);
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  const handleMarkAllRead = async () => {
    await notificationsApi.markAllAsRead();
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Retrouvez toutes les notifications liées à vos tickets."
        actions={
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck /> Tout marquer comme lu
          </Button>
        }
      />

      <Tabs value={filter} onValueChange={(value) => setFilter(value as "toutes" | "non-lues")} className="mb-4">
        <TabsList>
          <TabsTrigger value="toutes">Toutes</TabsTrigger>
          <TabsTrigger value="non-lues">Non lues</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-14 w-full" />)}
          </div>
        ) : !notifications || notifications.length === 0 ? (
          <EmptyState icon={Bell} title="Aucune notification" description="Vous n'avez aucune notification pour le moment." />
        ) : (
          <ul className="divide-y divide-border">
            {notifications.map((notification) => (
              <li key={notification.id} className={`flex items-start justify-between gap-4 px-4 py-3 ${notification.is_read ? "" : "bg-primary/5"}`}>
                <Link
                  href={notification.ticket_id ? `/tickets/${notification.ticket_id}` : "#"}
                  className="min-w-0 flex-1"
                  onClick={() => !notification.is_read && handleMarkAsRead(notification.id)}
                >
                  <p className="text-sm font-medium">{notification.title}</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">{notification.message}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
                    {NOTIFICATION_TYPE_LABELS[notification.type] ?? notification.type} · {formatDateTime(notification.created_at)}
                  </p>
                </Link>
                {!notification.is_read && (
                  <Button variant="ghost" size="sm" onClick={() => handleMarkAsRead(notification.id)} className="shrink-0 text-xs">
                    Marquer comme lu
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
