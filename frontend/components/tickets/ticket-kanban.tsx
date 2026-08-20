"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Inbox } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/common/empty-state";
import { TicketCard } from "@/components/tickets/ticket-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { useStatuses } from "@/hooks/use-reference-data";
import { getErrorMessage, ticketsApi } from "@/lib/api";
import { canTransition, MANAGED_ELSEWHERE_STATUSES } from "@/lib/ticket-transitions";
import type { TicketListItem } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Ordre d'affichage des colonnes : le flux actif de gauche à droite, puis les
 * statuts terminaux/gérés ailleurs. Miroir de app/models/status.py côté backend.
 */
const COLUMN_ORDER = ["Nouveau", "Ouvert", "En cours", "En attente", "Réouvert", "Résolu", "Fermé", "Annulé"];

interface TicketKanbanProps {
  tickets: TicketListItem[] | undefined;
  isLoading: boolean;
}

/**
 * Glisser-déposer natif (aucune dépendance ajoutée) : ne fait jamais qu'appeler
 * l'endpoint /tickets/{id}/status déjà existant, uniquement pour les transitions
 * que la machine à états backend autorise déjà (lib/ticket-transitions.ts, miroir
 * exact de ticket_state_machine.py). Résolu/Fermé restent en lecture seule ici :
 * ils exigent l'action dédiée (Résoudre/Fermer) sur la fiche ticket.
 */
export function TicketKanban({ tickets, isLoading }: TicketKanbanProps) {
  const { data: statuses } = useStatuses();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [draggedTicket, setDraggedTicket] = useState<TicketListItem | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);

  const columns = useMemo(() => {
    const byStatus = new Map<string, TicketListItem[]>();
    for (const name of COLUMN_ORDER) byStatus.set(name, []);
    for (const ticket of tickets ?? []) {
      const bucket = byStatus.get(ticket.status.name);
      if (bucket) bucket.push(ticket);
      else byStatus.set(ticket.status.name, [ticket]);
    }
    return Array.from(byStatus.entries());
  }, [tickets]);

  if (isLoading) {
    return (
      <div className="flex gap-3 overflow-x-auto p-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-96 w-72 shrink-0" />
        ))}
      </div>
    );
  }

  if (!tickets || tickets.length === 0) {
    return <EmptyState icon={Inbox} title="Aucun ticket trouvé" description="Aucun ticket ne correspond aux critères sélectionnés." />;
  }

  const handleDrop = async (targetStatusName: string) => {
    setDragOverColumn(null);
    const ticket = draggedTicket;
    setDraggedTicket(null);
    if (!ticket || ticket.status.name === targetStatusName) return;
    if (!canTransition(ticket.status.name, targetStatusName)) return;

    const targetStatus = statuses?.find((status) => status.name === targetStatusName);
    if (!targetStatus) return;

    try {
      await ticketsApi.changeStatus(ticket.id, targetStatus.id);
      toast({ title: `Ticket ${ticket.reference} déplacé vers « ${targetStatusName} ».` });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    }
  };

  return (
    <div className="flex gap-3 overflow-x-auto p-4">
      {columns.map(([statusName, columnTickets]) => {
        const isManagedElsewhere = MANAGED_ELSEWHERE_STATUSES.has(statusName);
        const isValidDropTarget = draggedTicket != null && canTransition(draggedTicket.status.name, statusName);
        const isDraggingOver = dragOverColumn === statusName;

        return (
          <div
            key={statusName}
            onDragOver={(event) => {
              if (!isValidDropTarget) return;
              event.preventDefault();
              setDragOverColumn(statusName);
            }}
            onDragLeave={() => setDragOverColumn((current) => (current === statusName ? null : current))}
            onDrop={(event) => {
              event.preventDefault();
              if (isValidDropTarget) void handleDrop(statusName);
            }}
            className={cn(
              "flex w-72 shrink-0 flex-col rounded-xl border bg-muted/30 transition-colors",
              isDraggingOver ? "border-primary bg-primary/5" : "border-border",
            )}
          >
            <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2.5">
              <span className="text-sm font-medium">{statusName}</span>
              <span className="rounded-full bg-card px-1.5 py-0.5 text-[11px] font-medium tabular-nums text-muted-foreground">
                {columnTickets.length}
              </span>
            </div>
            <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-2" style={{ maxHeight: "70vh" }}>
              {columnTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  draggable={!isManagedElsewhere}
                  onDragStart={() => setDraggedTicket(ticket)}
                  onDragEnd={() => {
                    setDraggedTicket(null);
                    setDragOverColumn(null);
                  }}
                  className={!isManagedElsewhere ? "cursor-grab active:cursor-grabbing" : undefined}
                  title={isManagedElsewhere ? "Utilisez l'action Résoudre / Fermer dédiée sur la fiche ticket." : undefined}
                >
                  <TicketCard ticket={ticket} />
                </div>
              ))}
              {columnTickets.length === 0 && (
                <p className="px-2 py-6 text-center text-xs text-muted-foreground">Aucun ticket</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
