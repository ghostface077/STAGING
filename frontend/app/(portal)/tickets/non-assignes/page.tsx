"use client";

import { useQuery } from "@tanstack/react-query";
import { LayoutGrid, Rows3 } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { TicketCardGrid } from "@/components/tickets/ticket-card";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ticketsApi } from "@/lib/api";

type View = "tableau" | "cartes";

export default function UnassignedTicketsPage() {
  const [view, setView] = useState<View>("cartes");

  // Sans pagination dédiée : page_size au maximum autorisé par l'API (100)
  // pour limiter le changement de comportement (correctif #07).
  const { data, isLoading } = useQuery({
    queryKey: ["tickets", "non-assignes"],
    queryFn: () => ticketsApi.list({ unassigned: true, page_size: 100 }).then((res) => res.data),
  });
  const tickets = data?.items;

  return (
    <div>
      <PageHeader
        title="Tickets non assignés"
        description="Tickets disponibles à prendre en charge."
        actions={
          <Tabs value={view} onValueChange={(value) => setView(value as View)}>
            <TabsList>
              <TabsTrigger value="cartes" className="gap-1.5"><LayoutGrid className="h-3.5 w-3.5" /> Cartes</TabsTrigger>
              <TabsTrigger value="tableau" className="gap-1.5"><Rows3 className="h-3.5 w-3.5" /> Tableau</TabsTrigger>
            </TabsList>
          </Tabs>
        }
      />
      <Card>
        {view === "tableau" ? (
          <TicketTable tickets={tickets} isLoading={isLoading} showTechnician={false} />
        ) : (
          <TicketCardGrid tickets={tickets} isLoading={isLoading} showTechnician={false} />
        )}
      </Card>
    </div>
  );
}
