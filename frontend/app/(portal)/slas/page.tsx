"use client";

import { useQuery } from "@tanstack/react-query";
import { Timer } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useSlas } from "@/hooks/use-reference-data";
import { ticketsApi } from "@/lib/api";

export default function SlasSupervisionPage() {
  const { data: slas, isLoading } = useSlas();

  // Vue de supervision sans pagination dédiée : page_size au maximum autorisé
  // par l'API (100) pour limiter le changement de comportement (correctif #07).
  const { data: allTicketsPage, isLoading: isLoadingTickets } = useQuery({
    queryKey: ["tickets", "sla-supervision"],
    queryFn: () => ticketsApi.list({ page_size: 100 }).then((res) => res.data),
  });
  const allTickets = allTicketsPage?.items;

  return (
    <div>
      <PageHeader title="Supervision des SLA" description="Configuration des délais et suivi des tickets sensibles." />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Configuration des SLA</CardTitle>
        </CardHeader>
        {isLoading ? (
          <CardContent><Skeleton className="h-32 w-full" /></CardContent>
        ) : !slas || slas.length === 0 ? (
          <CardContent><EmptyState icon={Timer} title="Aucun SLA configuré" /></CardContent>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Priorité</TableHead>
                <TableHead>Première réponse</TableHead>
                <TableHead>Résolution</TableHead>
                <TableHead>Statut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {slas.map((sla) => (
                <TableRow key={sla.id}>
                  <TableCell className="font-medium">{sla.name}</TableCell>
                  <TableCell>{sla.priority?.name}</TableCell>
                  <TableCell>{sla.first_response_minutes} min</TableCell>
                  <TableCell>{Math.round(sla.resolution_minutes / 60)} h</TableCell>
                  <TableCell>{sla.is_active ? "Actif" : "Inactif"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <p className="border-t border-border p-3 text-xs text-muted-foreground">
          La création et la modification des SLA se font depuis le back-office administrateur.
        </p>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tous les tickets sous SLA</CardTitle>
        </CardHeader>
        <TicketTable tickets={allTickets} isLoading={isLoadingTickets} />
      </Card>
    </div>
  );
}
