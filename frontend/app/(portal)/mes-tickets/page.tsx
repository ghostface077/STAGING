"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/common/page-header";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { ticketsApi } from "@/lib/api";

export default function MyTicketsPage() {
  const { user } = useAuth();
  const isRequesterView = user?.role?.name === "Utilisateur";

  // Sans pagination dédiée : page_size au maximum autorisé par l'API (100)
  // pour limiter le changement de comportement (correctif #07).
  const { data, isLoading } = useQuery({
    queryKey: ["tickets", "mes-tickets", user?.id],
    queryFn: () =>
      ticketsApi
        .list(isRequesterView ? { page_size: 100 } : { technician_id: user?.id, page_size: 100 })
        .then((res) => res.data),
    enabled: !!user,
  });
  const tickets = data?.items;

  return (
    <div>
      <PageHeader
        title="Mes tickets"
        description={isRequesterView ? "Les tickets que vous avez créés." : "Les tickets qui vous sont assignés."}
      />
      <Card>
        <TicketTable tickets={tickets} isLoading={isLoading} showRequester={!isRequesterView} showTechnician={isRequesterView} />
      </Card>
    </div>
  );
}
