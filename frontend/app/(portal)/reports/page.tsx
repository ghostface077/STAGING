"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock, Download, FileText, Star, Ticket } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { reportsApi } from "@/lib/api";

export default function ReportsPage() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data: summary, isLoading, refetch } = useQuery({
    queryKey: ["reports", "summary", dateFrom, dateTo],
    queryFn: () =>
      reportsApi.summary({ date_from: dateFrom || undefined, date_to: dateTo || undefined }).then((res) => res.data),
  });

  return (
    <div>
      <PageHeader
        title="Rapports"
        description="Statistiques détaillées du support sur une période donnée."
        actions={
          <Button asChild variant="outline">
            <a href={reportsApi.exportCsvUrl({ date_from: dateFrom || undefined, date_to: dateTo || undefined })} target="_blank" rel="noreferrer">
              <Download /> Exporter en CSV
            </a>
          </Button>
        }
      />

      <Card className="mb-6">
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end">
          <div className="space-y-1.5">
            <Label htmlFor="date_from">Du</Label>
            <Input id="date_from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="date_to">Au</Label>
            <Input id="date_to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          <Button onClick={() => refetch()}>
            <FileText /> Générer le rapport
          </Button>
        </CardContent>
      </Card>

      {isLoading || !summary ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => <Skeleton key={index} className="h-24" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard label="Total des tickets" value={summary.total_tickets} icon={Ticket} />
          <StatCard label="Tickets résolus" value={summary.tickets_resolus} icon={CheckCircle2} tone="success" />
          <StatCard label="Tickets ouverts" value={summary.tickets_ouverts} icon={Ticket} />
          <StatCard label="SLA dépassés" value={summary.tickets_sla_depasse} icon={Clock} tone="destructive" />
          <StatCard
            label="Temps moyen de résolution"
            value={summary.temps_moyen_resolution_heures !== null ? `${summary.temps_moyen_resolution_heures.toFixed(1)} h` : "—"}
            icon={Clock}
          />
          <StatCard
            label="Temps moyen 1ère réponse"
            value={summary.temps_moyen_premiere_reponse_minutes !== null ? `${Math.round(summary.temps_moyen_premiere_reponse_minutes)} min` : "—"}
            icon={Clock}
          />
          <StatCard
            label="Satisfaction moyenne"
            value={summary.satisfaction_moyenne !== null ? `${summary.satisfaction_moyenne.toFixed(1)} / 5` : "—"}
            icon={Star}
            tone="success"
          />
          <StatCard label="Tickets critiques" value={summary.tickets_critiques} icon={Ticket} tone="destructive" />
        </div>
      )}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Exports disponibles</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>L’export CSV est disponible ci-dessus (compatible Excel). Les exports PDF et Excel natifs sont prévus dans une prochaine version ; l’architecture du backend (endpoint <code className="rounded bg-muted px-1 py-0.5">/api/reports</code>) est déjà prête pour les accueillir.</p>
        </CardContent>
      </Card>
    </div>
  );
}
