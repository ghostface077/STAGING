"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { notificationsApi } from "@/lib/api";
import { NOTIFICATION_TYPE_LABELS } from "@/lib/constants";
import { notificationIcon } from "@/lib/notification-icons";
import type { Notification } from "@/lib/types";
import { dayBucketLabel, formatDateTime, formatRelativeTime } from "@/lib/utils";

const BUCKET_ORDER = ["Aujourd’hui", "Hier", "Cette semaine", "Plus ancien"] as const;

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"toutes" | "non-lues">("toutes");

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications", "all", filter],
    queryFn: () => notificationsApi.list(filter === "non-lues").then((res) => res.data),
  });

  const groups = useMemo(() => {
    const byBucket = new Map<string, Notification[]>();
    for (const notification of notifications ?? []) {
      const bucket = dayBucketLabel(notification.created_at);
      if (!byBucket.has(bucket)) byBucket.set(bucket, []);
      byBucket.get(bucket)!.push(notification);
    }
    return BUCKET_ORDER.map((bucket) => [bucket, byBucket.get(bucket) ?? []] as const).filter(([, items]) => items.length > 0);
  }, [notifications]);

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

      {isLoading ? (
        <Card>
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-16 w-full" />)}
          </div>
        </Card>
      ) : !notifications || notifications.length === 0 ? (
        <Card>
          <EmptyState icon={Bell} title="Aucune notification" description="Vous n'avez aucune notification pour le moment." />
        </Card>
      ) : (
        <div className="space-y-6">
          {groups.map(([bucket, items]) => (
            <div key={bucket}>
              <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{bucket}</p>
              <div className="space-y-2">
                {items.map((notification, index) => {
                  const Icon = notificationIcon(notification.type);
                  return (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.18, delay: Math.min(index, 8) * 0.03, ease: [0.16, 1, 0.3, 1] }}
                    >
                      <Card
                        className={`shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md ${
                          notification.is_read ? "" : "border-primary/30 bg-primary/[0.03]"
                        }`}
                      >
                        <div className="flex items-start gap-3 p-4">
                          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                            <Icon className="h-4 w-4" />
                          </div>
                          <Link
                            href={notification.ticket_id ? `/tickets/${notification.ticket_id}` : "#"}
                            className="min-w-0 flex-1"
                            onClick={() => !notification.is_read && handleMarkAsRead(notification.id)}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <p className="text-sm font-medium">{notification.title}</p>
                              {!notification.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />}
                            </div>
                            <p className="mt-0.5 text-sm text-muted-foreground">{notification.message}</p>
                            <p className="mt-1.5 text-xs uppercase tracking-wide text-muted-foreground" title={formatDateTime(notification.created_at)}>
                              {NOTIFICATION_TYPE_LABELS[notification.type] ?? notification.type} · {formatRelativeTime(notification.created_at)}
                            </p>
                          </Link>
                          {!notification.is_read && (
                            <Button variant="ghost" size="sm" onClick={() => handleMarkAsRead(notification.id)} className="shrink-0 text-xs">
                              Marquer comme lu
                            </Button>
                          )}
                        </div>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
