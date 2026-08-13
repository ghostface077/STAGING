"use client";

import { useQuery } from "@tanstack/react-query";
import { Building2, Database, Laptop, Server, Ticket, Users } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL, dashboardApi, departmentsApi, equipmentApi, usersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AdminSettingsPage() {
  const { user } = useAuth();

  // page_size=1 : seul le total nous intéresse ici, pas les éléments eux-mêmes.
  const { data: users } = useQuery({
    queryKey: ["users", "count"],
    queryFn: () => usersApi.list({ page_size: 1 }).then((r) => r.data),
  });
  const { data: departments } = useQuery({ queryKey: ["departments", "count"], queryFn: () => departmentsApi.list().then((r) => r.data) });
  const { data: equipmentList } = useQuery({
    queryKey: ["equipment", "count"],
    queryFn: () => equipmentApi.list({ page_size: 1 }).then((r) => r.data),
  });
  const { data: stats } = useQuery({ queryKey: ["dashboard", "statistics"], queryFn: () => dashboardApi.statistics().then((r) => r.data) });

  return (
    <div>
      <PageHeader title="Paramètres" description="Informations générales sur l'installation et l'état du système." />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Utilisateurs" value={users?.total ?? "—"} icon={Users} />
        <StatCard label="Services" value={departments?.length ?? "—"} icon={Building2} />
        <StatCard label="Équipements" value={equipmentList?.total ?? "—"} icon={Laptop} />
        <StatCard label="Tickets" value={stats?.total_tickets ?? "—"} icon={Ticket} />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><Server className="h-4 w-4" /> Informations système</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Row label="URL de l'API backend" value={API_BASE_URL} />
          <Row label="Compte administrateur connecté" value={`${user?.first_name} ${user?.last_name} (${user?.email})`} />
          <Row label="Documentation interactive de l'API" value="/api/docs (Swagger UI, servie par le backend FastAPI)" />
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><Database className="h-4 w-4" /> Gestion des données de référence</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>
            Les catégories, priorités, statuts, SLA, rôles et services se gèrent depuis les pages dédiées du menu latéral.
            Les mots de passe et secrets applicatifs sont configurés via les variables d’environnement du serveur (fichier
            <code className="mx-1 rounded bg-muted px-1 py-0.5">.env</code>) et ne sont jamais accessibles depuis cette interface.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col justify-between gap-1 border-b border-border py-2 last:border-0 sm:flex-row sm:items-center">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
