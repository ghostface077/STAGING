"use client";

import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";

import { HISTORY_ACTION_LABELS } from "@/lib/constants";
import { ticketsApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

export function HistoryTimeline({ ticketId }: { ticketId: number }) {
  const { data: history, isLoading } = useQuery({
    queryKey: ["tickets", ticketId, "history"],
    queryFn: () => ticketsApi.history(ticketId).then((res) => res.data),
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">Chargement de l’historique…</p>;
  if (!history || history.length === 0) return <p className="text-sm text-muted-foreground">Aucun historique disponible.</p>;

  return (
    <ol className="space-y-4">
      {history.map((entry) => (
        <li key={entry.id} className="flex gap-3">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <History className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1 border-b border-border pb-3">
            <p className="text-sm font-medium">{HISTORY_ACTION_LABELS[entry.action] ?? entry.action}</p>
            {(entry.old_value || entry.new_value) && (
              <p className="text-xs text-muted-foreground">
                {entry.old_value && <span>{entry.old_value} → </span>}
                {entry.new_value}
              </p>
            )}
            <p className="mt-0.5 text-xs text-muted-foreground">
              {entry.user ? `${entry.user.first_name} ${entry.user.last_name}` : "Système"} · {formatDateTime(entry.created_at)}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
