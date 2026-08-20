"use client";

import { motion } from "framer-motion";
import { Inbox } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/common/empty-state";
import { PriorityBadge } from "@/components/tickets/priority-badge";
import { SlaPill } from "@/components/tickets/sla-pill";
import { StatusBadge } from "@/components/tickets/status-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import type { TicketListItem } from "@/lib/types";
import { formatDateTime, getInitials } from "@/lib/utils";

interface TicketCardProps {
  ticket: TicketListItem;
  showRequester?: boolean;
  showTechnician?: boolean;
}

/** Carte premium pour un ticket : même information que la ligne de tableau, présentation vue Cartes/Kanban. */
export function TicketCard({ ticket, showRequester = true, showTechnician = true }: TicketCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
    >
      <Link
        href={`/tickets/${ticket.id}`}
        className="block rounded-xl border border-border bg-card p-4 shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md"
      >
        <div className="flex items-start justify-between gap-2">
          <p className="font-mono text-[11px] font-medium text-primary">{ticket.reference}</p>
          <PriorityBadge name={ticket.priority.name} />
        </div>
        <p className="mt-1.5 line-clamp-2 text-sm font-medium leading-snug">{ticket.title}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">{ticket.category.name}</p>

        <div className="mt-3 flex items-center justify-between gap-2">
          <StatusBadge name={ticket.status.name} />
          <SlaPill progress={ticket.sla_progress} />
        </div>

        <div className="mt-3 flex items-center justify-between gap-2 border-t border-border pt-3">
          {(showTechnician || showRequester) && (
            <div className="flex min-w-0 items-center gap-2">
              <Avatar className="h-6 w-6 shrink-0">
                <AvatarFallback className="text-[10px]">
                  {showTechnician
                    ? ticket.technician
                      ? getInitials(ticket.technician.first_name, ticket.technician.last_name)
                      : "?"
                    : getInitials(ticket.requester.first_name, ticket.requester.last_name)}
                </AvatarFallback>
              </Avatar>
              <span className="truncate text-xs text-muted-foreground">
                {showTechnician
                  ? ticket.technician
                    ? `${ticket.technician.first_name} ${ticket.technician.last_name}`
                    : "Non assigné"
                  : `${ticket.requester.first_name} ${ticket.requester.last_name}`}
              </span>
            </div>
          )}
          <span className="ml-auto shrink-0 whitespace-nowrap text-[11px] text-muted-foreground">{formatDateTime(ticket.created_at)}</span>
        </div>
      </Link>
    </motion.div>
  );
}

interface TicketCardGridProps {
  tickets: TicketListItem[] | undefined;
  isLoading: boolean;
  showRequester?: boolean;
  showTechnician?: boolean;
}

export function TicketCardGrid({ tickets, isLoading, showRequester = true, showTechnician = true }: TicketCardGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-40 w-full" />
        ))}
      </div>
    );
  }

  if (!tickets || tickets.length === 0) {
    return <EmptyState icon={Inbox} title="Aucun ticket trouvé" description="Aucun ticket ne correspond aux critères sélectionnés." />;
  }

  return (
    <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 xl:grid-cols-3">
      {tickets.map((ticket) => (
        <TicketCard key={ticket.id} ticket={ticket} showRequester={showRequester} showTechnician={showTechnician} />
      ))}
    </div>
  );
}
