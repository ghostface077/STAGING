"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/common/page-header";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card } from "@/components/ui/card";
import { ticketsApi } from "@/lib/api";

export default function UnassignedTicketsPage() {
  // Sans pagination dédiée : page_size au maximum autorisé par l'API (100)
  // pour limiter le changement de comportement (correctif #07).
  const { data, isLoading } = useQuery({
    queryKey: ["tickets", "non-assignes"],
    queryFn: () => ticketsApi.list({ unassigned: true, page_size: 100 }).then((res) => res.data),
  });
  const tickets = data?.items;

  return (
    <div>
      <PageHeader title="Tickets non assignés" description="Tickets disponibles à prendre en charge." />
      <Card>
        <TicketTable tickets={tickets} isLoading={isLoading} showTechnician={false} />
      </Card>
    </div>
  );
}
