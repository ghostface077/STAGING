"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { CommentThread } from "@/components/tickets/comment-thread";
import { HistoryTimeline } from "@/components/tickets/history-timeline";
import { PriorityBadge } from "@/components/tickets/priority-badge";
import { SatisfactionWidget } from "@/components/tickets/satisfaction-widget";
import { SlaIndicator } from "@/components/tickets/sla-indicator";
import { StatusBadge } from "@/components/tickets/status-badge";
import { TicketActions } from "@/components/tickets/ticket-actions";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { ticketsApi } from "@/lib/api";
import { formatDateTime, getInitials } from "@/lib/utils";

export default function TicketDetailPage() {
  const params = useParams<{ id: string }>();
  const ticketId = Number(params.id);
  const { user } = useAuth();

  const { data: ticket, isLoading, isError } = useQuery({
    queryKey: ["tickets", ticketId],
    queryFn: () => ticketsApi.get(ticketId).then((res) => res.data),
    enabled: Number.isFinite(ticketId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !ticket) {
    return <p className="text-sm text-destructive">Impossible de charger ce ticket. Vérifiez que vous y avez accès.</p>;
  }

  const role = user?.role?.name;
  const canWriteInternal = role === "Technicien" || role === "Responsable IT" || role === "Administrateur";
  const isRequester = ticket.requester.id === user?.id;
  const canRate = isRequester && (ticket.status.name === "Résolu" || ticket.status.name === "Fermé");
  const canSeeAllTickets = role === "Responsable IT" || role === "Administrateur";
  const backHref = canSeeAllTickets ? "/tickets" : "/mes-tickets";
  const backLabel = canSeeAllTickets ? "Tous les tickets" : "Mes tickets";

  return (
    <div className="space-y-6">
      <Link href={backHref} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> {backLabel}
      </Link>

      <Card>
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="font-mono text-xs font-medium text-muted-foreground">{ticket.reference}</p>
            <h1 className="mt-0.5 text-xl font-semibold tracking-tight sm:text-2xl">{ticket.title}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge name={ticket.status.name} />
              <PriorityBadge name={ticket.priority.name} />
              <span className="text-xs text-muted-foreground">·</span>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Avatar className="h-5 w-5"><AvatarFallback className="text-[9px]">{getInitials(ticket.requester.first_name, ticket.requester.last_name)}</AvatarFallback></Avatar>
                {ticket.requester.first_name} {ticket.requester.last_name}
              </div>
              {ticket.technician && (
                <>
                  <span className="text-xs text-muted-foreground">→</span>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Avatar className="h-5 w-5"><AvatarFallback className="text-[9px]">{getInitials(ticket.technician.first_name, ticket.technician.last_name)}</AvatarFallback></Avatar>
                    {ticket.technician.first_name} {ticket.technician.last_name}
                  </div>
                </>
              )}
            </div>
          </div>
          {user && role && <TicketActions ticket={ticket} currentUserId={user.id} role={role} />}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{ticket.description}</p>
            </CardContent>
          </Card>

          {ticket.solution && (
            <Card className="border-success/40 bg-success/5">
              <CardHeader>
                <CardTitle className="text-base text-success">Solution apportée</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{ticket.solution}</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardContent className="p-4">
              <Tabs defaultValue="conversation">
                <TabsList>
                  <TabsTrigger value="conversation">Conversation</TabsTrigger>
                  <TabsTrigger value="historique">Historique</TabsTrigger>
                </TabsList>
                <TabsContent value="conversation">
                  <CommentThread ticketId={ticket.id} canWriteInternal={canWriteInternal} />
                </TabsContent>
                <TabsContent value="historique">
                  <HistoryTimeline ticketId={ticket.id} />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {canRate && <SatisfactionWidget ticketId={ticket.id} />}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">SLA</CardTitle>
            </CardHeader>
            <CardContent>
              <SlaIndicator progress={ticket.sla_progress} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Informations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <InfoRow label="Catégorie" value={ticket.category.name} />
              <InfoRow label="Utilisateur" value={`${ticket.requester.first_name} ${ticket.requester.last_name}`} />
              <InfoRow label="Technicien" value={ticket.technician ? `${ticket.technician.first_name} ${ticket.technician.last_name}` : "Non assigné"} />
              <InfoRow label="Équipe" value={ticket.team?.name ?? "Aucune"} />
              <InfoRow label="Date de création" value={formatDateTime(ticket.created_at)} />
              <InfoRow label="Date de résolution" value={formatDateTime(ticket.resolved_at)} />
              <InfoRow label="Date de fermeture" value={formatDateTime(ticket.closed_at)} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
