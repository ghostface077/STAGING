"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Clock, Gauge, ListTodo, ShieldAlert, Star, Ticket } from "lucide-react";
import dynamic from "next/dynamic";

import { RecentActivity } from "@/components/dashboard/recent-activity";
import { StatCard } from "@/components/common/stat-card";
import { PageHeader } from "@/components/common/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth-context";
import { dashboardApi } from "@/lib/api";
import { formatDurationMinutes } from "@/lib/utils";

// Recharts est une dépendance lourde et ne sait pas se rendre côté serveur :
// chargée à la demande dans son propre chunk plutôt que dans le bundle initial.
const ChartSkeleton = () => <Skeleton className="h-[260px]" />;
const StatusBarChart = dynamic(() => import("@/components/dashboard/status-bar-chart").then((mod) => mod.StatusBarChart), {
  ssr: false,
  loading: ChartSkeleton,
});
const PriorityPieChart = dynamic(() => import("@/components/dashboard/priority-pie-chart").then((mod) => mod.PriorityPieChart), {
  ssr: false,
  loading: ChartSkeleton,
});

export default function DashboardPage() {
  const { user } = useAuth();
  const role = user?.role?.name;
  const isStaff = role === "Technicien" || role === "Responsable IT" || role === "Administrateur";

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard", "statistics"],
    queryFn: () => dashboardApi.statistics().then((res) => res.data),
  });
  const { data: byStatus, isLoading: isLoadingByStatus } = useQuery({
    queryKey: ["dashboard", "by-status"],
    queryFn: () => dashboardApi.byStatus().then((res) => res.data),
  });
  const { data: byPriority, isLoading: isLoadingByPriority } = useQuery({
    queryKey: ["dashboard", "by-priority"],
    queryFn: () => dashboardApi.byPriority().then((res) => res.data),
  });
  const { data: slaOverview } = useQuery({
    queryKey: ["dashboard", "sla"],
    queryFn: () => dashboardApi.slaOverview().then((res) => res.data),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Bonjour, ${user?.first_name ?? ""} 👋`}
        description={role === "Utilisateur" ? "Voici un aperçu de vos demandes en cours." : "Voici l'état actuel du support informatique."}
      />

      {/* Indicateurs clés */}
      {isLoading || !stats ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-28" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard size="lg" label="Total des tickets" value={stats.total_tickets} icon={Ticket} />
          <StatCard size="lg" label="En cours de traitement" value={stats.tickets_en_cours} icon={Gauge} tone="info" />
          <StatCard size="lg" label="Critiques actifs" value={stats.tickets_critiques} icon={AlertTriangle} tone="destructive" />
          <StatCard size="lg" label="SLA dépassés" value={stats.tickets_sla_depasse} icon={ShieldAlert} tone="warning" />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Colonne principale : graphiques + performance */}
        <div className="space-y-6 lg:col-span-2">
          {!isLoading && stats && (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard label="Ouverts" value={stats.tickets_ouverts} icon={ListTodo} />
              <StatCard label="En attente" value={stats.tickets_en_attente} icon={Clock} tone="warning" />
              <StatCard label="Résolus" value={stats.tickets_resolus} icon={CheckCircle2} tone="success" />
              <StatCard
                label="Satisfaction"
                value={stats.satisfaction_moyenne !== null ? `${stats.satisfaction_moyenne.toFixed(1)}/5` : "—"}
                icon={Star}
                tone="brand"
              />
            </div>
          )}

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Card className="shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
              <CardHeader>
                <CardTitle className="text-base">Tickets par statut</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingByStatus ? <Skeleton className="h-[260px]" /> : <StatusBarChart data={byStatus ?? []} />}
              </CardContent>
            </Card>
            <Card className="shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
              <CardHeader>
                <CardTitle className="text-base">Tickets par priorité</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingByPriority ? <Skeleton className="h-[260px]" /> : <PriorityPieChart data={byPriority ?? []} />}
              </CardContent>
            </Card>
          </div>

          {isStaff && stats && (
            <Card className="shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
              <CardHeader>
                <CardTitle className="text-base">Performance du support</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <PerformanceMetric
                    label="Temps moyen de 1ère réponse"
                    value={stats.temps_moyen_premiere_reponse_minutes !== null ? formatDurationMinutes(Math.round(stats.temps_moyen_premiere_reponse_minutes)) : "—"}
                  />
                  <PerformanceMetric
                    label="Temps moyen de résolution"
                    value={stats.temps_moyen_resolution_heures !== null ? `${stats.temps_moyen_resolution_heures.toFixed(1)} h` : "—"}
                  />
                  <PerformanceMetric
                    label="Respect des SLA"
                    value={slaOverview ? `${slaOverview.taux_respect_pourcent}%` : "—"}
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Colonne latérale : activité récente */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">Activité récente</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentActivity />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function PerformanceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}
