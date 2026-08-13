"use client";

import { useQuery } from "@tanstack/react-query";
import { UserCog } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dashboardApi } from "@/lib/api";

/** Initiales calculées à partir du nom complet retourné par l'API statistiques (ex : "Fatou Ndiaye" → "FN"). */
function initialsFromFullName(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  const first = parts[0]?.charAt(0) ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1].charAt(0) : "";
  return `${first}${last}`.toUpperCase();
}

export default function TechniciansPage() {
  const { data: technicians, isLoading } = useQuery({
    queryKey: ["dashboard", "by-technician"],
    queryFn: () => dashboardApi.byTechnician().then((res) => res.data),
  });

  return (
    <div>
      <PageHeader title="Techniciens" description="Performance et charge de travail de chaque technicien." />

      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-12 w-full" />)}
          </div>
        ) : !technicians || technicians.length === 0 ? (
          <EmptyState icon={UserCog} title="Aucun technicien" description="Aucun technicien n'est encore enregistré." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Technicien</TableHead>
                <TableHead>Tickets assignés</TableHead>
                <TableHead>Tickets résolus</TableHead>
                <TableHead>Temps moyen de résolution</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {technicians.map((technician) => (
                <TableRow key={technician.technician_id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Avatar className="h-7 w-7">
                        <AvatarFallback className="text-xs">{initialsFromFullName(technician.technician_name)}</AvatarFallback>
                      </Avatar>
                      {technician.technician_name}
                    </div>
                  </TableCell>
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
  );
}
