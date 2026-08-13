"use client";

import { Inbox } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/common/empty-state";
import { PriorityBadge } from "@/components/tickets/priority-badge";
import { SlaPill } from "@/components/tickets/sla-pill";
import { StatusBadge } from "@/components/tickets/status-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TicketListItem } from "@/lib/types";
import { formatDateTime, getInitials } from "@/lib/utils";

interface TicketTableProps {
  tickets: TicketListItem[] | undefined;
  isLoading: boolean;
  showRequester?: boolean;
  showTechnician?: boolean;
}

export function TicketTable({ tickets, isLoading, showRequester = true, showTechnician = true }: TicketTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (!tickets || tickets.length === 0) {
    return <EmptyState icon={Inbox} title="Aucun ticket trouvé" description="Aucun ticket ne correspond aux critères sélectionnés." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ticket</TableHead>
          <TableHead>Statut</TableHead>
          <TableHead>Priorité</TableHead>
          {showRequester && <TableHead>Demandeur</TableHead>}
          {showTechnician && <TableHead>Technicien</TableHead>}
          <TableHead>SLA</TableHead>
          <TableHead>Créé le</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tickets.map((ticket) => (
          <TableRow key={ticket.id} className="cursor-pointer">
            <TableCell className="max-w-[320px] py-3">
              <Link href={`/tickets/${ticket.id}`} className="block">
                <p className="font-mono text-[11px] font-medium text-primary">{ticket.reference}</p>
                <p className="line-clamp-1 text-sm font-medium leading-snug">{ticket.title}</p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">{ticket.category.name}</p>
              </Link>
            </TableCell>
            <TableCell>
              <StatusBadge name={ticket.status.name} />
            </TableCell>
            <TableCell>
              <PriorityBadge name={ticket.priority.name} />
            </TableCell>
            {showRequester && (
              <TableCell>
                <div className="flex items-center gap-2">
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-[10px]">{getInitials(ticket.requester.first_name, ticket.requester.last_name)}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{ticket.requester.first_name} {ticket.requester.last_name}</span>
                </div>
              </TableCell>
            )}
            {showTechnician && (
              <TableCell className="text-sm">
                {ticket.technician ? (
                  <div className="flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="text-[10px]">{getInitials(ticket.technician.first_name, ticket.technician.last_name)}</AvatarFallback>
                    </Avatar>
                    <span>{ticket.technician.first_name} {ticket.technician.last_name}</span>
                  </div>
                ) : (
                  <span className="text-muted-foreground">Non assigné</span>
                )}
              </TableCell>
            )}
            <TableCell>
              <SlaPill progress={ticket.sla_progress} />
            </TableCell>
            <TableCell className="whitespace-nowrap text-sm text-muted-foreground">{formatDateTime(ticket.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
