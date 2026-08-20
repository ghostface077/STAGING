"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpCircle,
  CheckCircle2,
  History,
  MessageSquare,
  Paperclip,
  Pencil,
  PlusCircle,
  RotateCcw,
  UserCheck,
  UserPlus,
  Workflow,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { HISTORY_ACTION_LABELS } from "@/lib/constants";
import { ticketsApi } from "@/lib/api";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";

const ACTION_ICONS: Record<string, LucideIcon> = {
  creation: PlusCircle,
  modification: Pencil,
  attribution: UserPlus,
  prise_en_charge: UserCheck,
  changement_statut: Workflow,
  changement_priorite: AlertTriangle,
  commentaire: MessageSquare,
  resolution: CheckCircle2,
  fermeture: XCircle,
  reouverture: RotateCcw,
  escalade: ArrowUpCircle,
  ajout_piece_jointe: Paperclip,
};

export function HistoryTimeline({ ticketId }: { ticketId: number }) {
  const { data: history, isLoading } = useQuery({
    queryKey: ["tickets", ticketId, "history"],
    queryFn: () => ticketsApi.history(ticketId).then((res) => res.data),
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">Chargement de l’historique…</p>;
  if (!history || history.length === 0) return <p className="text-sm text-muted-foreground">Aucun historique disponible.</p>;

  return (
    <ol className="relative space-y-4">
      {history.map((entry, index) => {
        const Icon = ACTION_ICONS[entry.action] ?? History;
        const isLast = index === history.length - 1;
        return (
          <motion.li
            key={entry.id}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: Math.min(index, 8) * 0.04, ease: [0.16, 1, 0.3, 1] }}
            className="relative flex gap-3"
          >
            {!isLast && <span className="absolute left-3 top-6 h-[calc(100%-0.5rem)] w-px -translate-x-1/2 bg-border" aria-hidden />}
            <div className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1 pb-1">
              <p className="text-sm font-medium">{HISTORY_ACTION_LABELS[entry.action] ?? entry.action}</p>
              {(entry.old_value || entry.new_value) && (
                <p className="text-xs text-muted-foreground">
                  {entry.old_value && <span>{entry.old_value} → </span>}
                  {entry.new_value}
                </p>
              )}
              <p className="mt-0.5 text-xs text-muted-foreground" title={formatDateTime(entry.created_at)}>
                {entry.user ? `${entry.user.first_name} ${entry.user.last_name}` : "Système"} · {formatRelativeTime(entry.created_at)}
              </p>
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
