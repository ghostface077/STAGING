"use client";

import { useQuery } from "@tanstack/react-query";
import { FileClock } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { auditLogsApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

export default function AdminAuditLogsPage() {
  const [entityType, setEntityType] = useState("");

  const { data: logs, isLoading } = useQuery({
    queryKey: ["audit-logs", entityType],
    queryFn: () => auditLogsApi.list({ entity_type: entityType || undefined }).then((res) => res.data),
  });

  return (
    <div>
      <PageHeader title="Journal d'audit" description="Historique de toutes les actions sensibles effectuées sur la plateforme." />

      <div className="mb-4 max-w-xs">
        <Input value={entityType} onChange={(event) => setEntityType(event.target.value)} placeholder="Filtrer par type d'entité (ex : ticket, user)…" />
      </div>

      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !logs || logs.length === 0 ? (
          <EmptyState icon={FileClock} title="Aucune entrée d'audit" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Utilisateur</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entité</TableHead>
                <TableHead>Adresse IP</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap text-sm text-muted-foreground">{formatDateTime(log.created_at)}</TableCell>
                  <TableCell className="text-sm">{log.user ? `${log.user.first_name} ${log.user.last_name}` : "Système"}</TableCell>
                  <TableCell><Badge variant="outline">{log.action}</Badge></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{log.entity_type} {log.entity_id ? `#${log.entity_id}` : ""}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{log.ip_address ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
