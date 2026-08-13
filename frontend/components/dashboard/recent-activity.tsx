"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  CheckCircle2,
  MessageSquare,
  RotateCcw,
  ShieldAlert,
  UserPlus,
  XCircle,
} from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { notificationsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

const ACTIVITY_ICONS: Record<string, typeof Bell> = {
  creation_ticket: Bell,
  attribution: UserPlus,
  nouveau_commentaire: MessageSquare,
  changement_statut: RotateCcw,
  changement_priorite: ShieldAlert,
  resolution: CheckCircle2,
  fermeture: XCircle,
  reouverture: RotateCcw,
  sla_bientot_depasse: ShieldAlert,
  sla_depasse: ShieldAlert,
};

/** Fil d'activité récente basé sur les notifications réellement générées par le backend. */
export function RecentActivity() {
  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications", "activity-feed"],
    queryFn: () => notificationsApi.list().then((res) => res.data.slice(0, 7)),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
            <Skeleton className="h-4 flex-1" />
          </div>
        ))}
      </div>
    );
  }

  if (!notifications || notifications.length === 0) {
    return <EmptyState icon={Bell} title="Aucune activité récente" description="Les actions sur vos tickets apparaîtront ici." />;
  }

  return (
    <ol className="space-y-1">
      {notifications.map((notification) => {
        const Icon = ACTIVITY_ICONS[notification.type] ?? Bell;
        const content = (
          <div className="flex items-start gap-3 rounded-md px-2 py-2 transition-colors hover:bg-accent">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium leading-tight">{notification.title}</p>
              <p className="truncate text-xs text-muted-foreground">{notification.message}</p>
            </div>
            <span className="shrink-0 whitespace-nowrap text-xs text-muted-foreground">
              {formatRelativeTime(notification.created_at)}
            </span>
          </div>
        );
        return (
          <li key={notification.id}>
            {notification.ticket_id ? (
              <Link href={`/tickets/${notification.ticket_id}`}>{content}</Link>
            ) : (
              content
            )}
          </li>
        );
      })}
    </ol>
  );
}
