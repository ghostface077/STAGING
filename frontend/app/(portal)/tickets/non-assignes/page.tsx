"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/common/page-header";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card } from "@/components/ui/card";
import { ticketsApi } from "@/lib/api";

export default function UnassignedTicketsPage() {
  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets", "non-assignes"],
    queryFn: () => ticketsApi.list({ unassigned: true }).then((res) => res.data),
  });

  return (
    <div>
      <PageHeader title="Tickets non assignés" description="Tickets disponibles à prendre en charge." />
      <Card>
        <TicketTable tickets={tickets} isLoading={isLoading} showTechnician={false} />
      </Card>
    </div>
  );
}
