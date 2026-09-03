"use client";

import { useQuery } from "@tanstack/react-query";
import { LayoutGrid, Rows3 } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { TicketCardGrid } from "@/components/tickets/ticket-card";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { ticketsApi } from "@/lib/api";

type View = "tableau" | "cartes";

export default function MyTicketsPage() {
  const { user } = useAuth();
  const isRequesterView = user?.role?.name === "Utilisateur";
  const [view, setView] = useState<View>("tableau");

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
        title={isRequesterView ? "Mes tickets" : "Tickets assignés"}
        description={isRequesterView ? "Les tickets que vous avez créés." : "Les tickets qui vous sont assignés."}
        actions={
          <Tabs value={view} onValueChange={(value) => setView(value as View)}>
            <TabsList>
              <TabsTrigger value="tableau" className="gap-1.5"><Rows3 className="h-3.5 w-3.5" /> Tableau</TabsTrigger>
              <TabsTrigger value="cartes" className="gap-1.5"><LayoutGrid className="h-3.5 w-3.5" /> Cartes</TabsTrigger>
            </TabsList>
          </Tabs>
        }
      />
      <Card>
        {view === "tableau" ? (
          <TicketTable tickets={tickets} isLoading={isLoading} showRequester={!isRequesterView} showTechnician={isRequesterView} />
        ) : (
          <TicketCardGrid tickets={tickets} isLoading={isLoading} showRequester={!isRequesterView} showTechnician={isRequesterView} />
        )}
      </Card>
    </div>
  );
}
