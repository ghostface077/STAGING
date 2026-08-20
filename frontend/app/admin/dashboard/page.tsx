"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Clock, Gauge, ShieldAlert, Star, Ticket, UserCog } from "lucide-react";
import dynamic from "next/dynamic";

import { AdminRecentActivity } from "@/components/dashboard/admin-recent-activity";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dashboardApi } from "@/lib/api";

// Recharts chargé à la demande, hors du bundle initial (même traitement que le tableau de bord portail).
const ChartSkeleton = () => <Skeleton className="h-[260px]" />;
const CategoryBarChart = dynamic(() => import("@/components/dashboard/category-bar-chart").then((mod) => mod.CategoryBarChart), {
  ssr: false,
  loading: ChartSkeleton,
});
const PriorityPieChart = dynamic(() => import("@/components/dashboard/priority-pie-chart").then((mod) => mod.PriorityPieChart), {
  ssr: false,
  loading: ChartSkeleton,
});
const StatusBarChart = dynamic(() => import("@/components/dashboard/status-bar-chart").then((mod) => mod.StatusBarChart), {
  ssr: false,
  loading: ChartSkeleton,
});

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard", "statistics"],
    queryFn: () => dashboardApi.statistics().then((res) => res.data),
  });
  const { data: byStatus } = useQuery({ queryKey: ["dashboard", "by-status"], queryFn: () => dashboardApi.byStatus().then((r) => r.data) });
  const { data: byPriority } = useQuery({ queryKey: ["dashboard", "by-priority"], queryFn: () => dashboardApi.byPriority().then((r) => r.data) });
  const { data: byCategory } = useQuery({ queryKey: ["dashboard", "by-category"], queryFn: () => dashboardApi.byCategory().then((r) => r.data) });
  const { data: byTechnician, isLoading: isLoadingTech } = useQuery({
    queryKey: ["dashboard", "by-technician"],
    queryFn: () => dashboardApi.byTechnician().then((r) => r.data),
  });
  const { data: sla } = useQuery({ queryKey: ["dashboard", "sla"], queryFn: () => dashboardApi.slaOverview().then((r) => r.data) });

  return (
    <div className="space-y-6">
      <PageHeader title="Tableau de bord administrateur" description="Vue d'ensemble globale de la plateforme IT Support." />

      {isLoading || !stats ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-28" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard size="lg" label="Total des tickets" value={stats.total_tickets} icon={Ticket} />
          <StatCard size="lg" label="Tickets en cours" value={stats.tickets_en_cours} icon={Gauge} tone="info" />
          <StatCard size="lg" label="Tickets critiques" value={stats.tickets_critiques} icon={AlertTriangle} tone="destructive" />
          <StatCard size="lg" label="SLA dépassés" value={stats.tickets_sla_depasse} icon={ShieldAlert} tone="warning" />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Card className="shadow-premium-sm">
              <CardHeader><CardTitle className="text-base">Tickets par statut</CardTitle></CardHeader>
              <CardContent><StatusBarChart data={byStatus ?? []} /></CardContent>
            </Card>
            <Card className="shadow-premium-sm">
              <CardHeader><CardTitle className="text-base">Tickets par priorité</CardTitle></CardHeader>
              <CardContent><PriorityPieChart data={byPriority ?? []} /></CardContent>
            </Card>
          </div>

          <Card className="shadow-premium-sm">
            <CardHeader><CardTitle className="text-base">Tickets par catégorie</CardTitle></CardHeader>
            <CardContent><CategoryBarChart data={byCategory ?? []} /></CardContent>
          </Card>

          {sla && (
            <Card className="shadow-premium-sm">
              <CardHeader><CardTitle className="text-base">Respect des SLA</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard label="Respectés" value={sla.respectes} icon={CheckCircle2} tone="success" />
                  <StatCard label="Bientôt dépassés" value={sla.bientot_depasses} icon={Clock} tone="warning" />
                  <StatCard label="Dépassés" value={sla.depasses} icon={ShieldAlert} tone="destructive" />
                  <StatCard label="Taux de respect" value={`${sla.taux_respect_pourcent}%`} icon={ShieldAlert} tone="success" />
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="shadow-premium-sm">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2"><UserCog className="h-4 w-4" /> Performance par technicien</CardTitle>
            </CardHeader>
            {isLoadingTech ? (
              <CardContent><Skeleton className="h-32 w-full" /></CardContent>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Technicien</TableHead>
                    <TableHead>Assignés</TableHead>
                    <TableHead>Résolus</TableHead>
                    <TableHead>Temps moyen de résolution</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {byTechnician?.map((technician) => (
                    <TableRow key={technician.technician_id}>
                      <TableCell className="font-medium">{technician.technician_name}</TableCell>
                      <TableCell>{technician.tickets_assignes}</TableCell>
                      <TableCell>{technician.tickets_resolus}</TableCell>
                      <TableCell>{technician.temps_moyen_resolution_heures !== null ? `${technician.temps_moyen_resolution_heures.toFixed(1)} h` : "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="shadow-premium-sm">
            <CardHeader><CardTitle className="text-base">Activité système récente</CardTitle></CardHeader>
            <CardContent><AdminRecentActivity /></CardContent>
          </Card>

          {stats && (
            <Card className="shadow-premium-sm">
              <CardHeader><CardTitle className="text-base">Synthèse</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <StatCard label="Temps moyen 1ère réponse" value={stats.temps_moyen_premiere_reponse_minutes !== null ? `${Math.round(stats.temps_moyen_premiere_reponse_minutes)} min` : "—"} icon={Clock} />
                <StatCard label="Temps moyen de résolution" value={stats.temps_moyen_resolution_heures !== null ? `${stats.temps_moyen_resolution_heures.toFixed(1)} h` : "—"} icon={Gauge} />
                <StatCard label="Satisfaction moyenne" value={stats.satisfaction_moyenne !== null ? `${stats.satisfaction_moyenne.toFixed(1)} / 5` : "—"} icon={Star} tone="brand" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
