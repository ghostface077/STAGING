"use client";

import { useQuery } from "@tanstack/react-query";
import { FileClock } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { auditLogsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

/** Fil d'activité système pour le dashboard administrateur, basé sur le journal d'audit réel. */
export function AdminRecentActivity() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ["audit-logs", "activity-feed"],
    queryFn: () => auditLogsApi.list().then((res) => res.data.slice(0, 8)),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-8 w-full" />)}
      </div>
    );
  }

  if (!logs || logs.length === 0) {
    return <EmptyState icon={FileClock} title="Aucune activité récente" />;
  }

  return (
    <ol className="space-y-1">
      {logs.map((log) => (
        <li key={log.id} className="flex items-center justify-between gap-3 rounded-md px-2 py-2 text-sm hover:bg-accent">
          <div className="min-w-0">
            <span className="font-medium">{log.user ? `${log.user.first_name} ${log.user.last_name}` : "Système"}</span>{" "}
            <Badge variant="outline" className="align-middle text-[10px]">{log.action}</Badge>
          </div>
          <span className="shrink-0 whitespace-nowrap text-xs text-muted-foreground">{formatRelativeTime(log.created_at)}</span>
        </li>
      ))}
    </ol>
  );
}
