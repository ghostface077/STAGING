"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Laptop, Loader2, Plus, Search } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import { useDepartments } from "@/hooks/use-reference-data";
import { equipmentApi, getErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Equipment } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const PAGE_SIZE = 20;

const equipmentSchema = z.object({
  asset_number: z.string().min(1, "Le numéro d'actif est obligatoire."),
  type: z.string().min(1, "Le type est obligatoire."),
  brand: z.string().min(1, "La marque est obligatoire."),
  model: z.string().min(1, "Le modèle est obligatoire."),
  serial_number: z.string().optional(),
  department_id: z.string().optional(),
  operating_system: z.string().optional(),
});
type EquipmentFormValues = z.infer<typeof equipmentSchema>;

export default function EquipmentPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: departments } = useDepartments();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Equipment | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isManager = user?.role?.name === "Responsable IT" || user?.role?.name === "Administrateur";

  const { data, isLoading } = useQuery({
    queryKey: ["equipment", { search, page }],
    queryFn: () =>
      equipmentApi.list({ search: search || undefined, page, page_size: PAGE_SIZE }).then((res) => res.data),
    placeholderData: (previous) => previous,
  });
  const equipmentList = data?.items;

  const { data: equipmentTickets, isLoading: isLoadingTickets } = useQuery({
    queryKey: ["equipment", selected?.id, "tickets"],
    queryFn: () => equipmentApi.tickets(selected!.id).then((res) => res.data),
    enabled: !!selected,
  });

  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<EquipmentFormValues>({
    resolver: zodResolver(equipmentSchema),
  });

  const onSubmit = async (values: EquipmentFormValues) => {
    setIsSubmitting(true);
    try {
      await equipmentApi.create({
        ...values,
        department_id: values.department_id ? Number(values.department_id) : null,
      });
      toast({ title: "Équipement ajouté avec succès." });
      queryClient.invalidateQueries({ queryKey: ["equipment"] });
      setIsCreateOpen(false);
      reset();
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Équipements"
        description="Parc informatique de l'organisation."
        actions={
          isManager ? (
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus /> Ajouter un équipement
            </Button>
          ) : undefined
        }
      />

      <div className="relative mb-4 max-w-md">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          placeholder="Rechercher par numéro d'actif, marque, modèle…"
          className="pl-8"
        />
      </div>

      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-12 w-full" />)}
          </div>
        ) : !equipmentList || equipmentList.length === 0 ? (
          <EmptyState icon={Laptop} title="Aucun équipement" description="Aucun équipement ne correspond à votre recherche." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Numéro d’actif</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Marque / Modèle</TableHead>
                <TableHead>Utilisateur</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Garantie</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {equipmentList.map((equipment) => (
                <TableRow key={equipment.id} className="cursor-pointer" onClick={() => setSelected(equipment)}>
                  <TableCell className="font-mono text-xs font-medium">{equipment.asset_number}</TableCell>
                  <TableCell>{equipment.type}</TableCell>
                  <TableCell>{equipment.brand} {equipment.model}</TableCell>
                  <TableCell>{equipment.user ? `${equipment.user.first_name} ${equipment.user.last_name}` : "—"}</TableCell>
                  <TableCell>{equipment.department?.name ?? "—"}</TableCell>
                  <TableCell><Badge variant="outline">{equipment.status}</Badge></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{formatDate(equipment.warranty_end_date)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <Pagination page={page} pageCount={data?.pages ?? 1} onPageChange={setPage} totalItems={data?.total} pageSize={PAGE_SIZE} />
      </Card>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-2xl">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle>{selected.asset_number} — {selected.brand} {selected.model}</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <InfoRow label="Type" value={selected.type} />
                <InfoRow label="Numéro de série" value={selected.serial_number ?? "—"} />
                <InfoRow label="Utilisateur" value={selected.user ? `${selected.user.first_name} ${selected.user.last_name}` : "—"} />
                <InfoRow label="Service" value={selected.department?.name ?? "—"} />
                <InfoRow label="Système d’exploitation" value={selected.operating_system ?? "—"} />
                <InfoRow label="Statut" value={selected.status} />
                <InfoRow label="Date d'achat" value={formatDate(selected.purchase_date)} />
                <InfoRow label="Fin de garantie" value={formatDate(selected.warranty_end_date)} />
              </div>
              <div>
                <p className="mb-2 text-sm font-semibold">Historique des tickets associés</p>
                <div className="max-h-64 overflow-y-auto rounded-md border border-border">
                  <TicketTable tickets={equipmentTickets} isLoading={isLoadingTickets} showRequester />
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Ajouter un équipement</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="asset_number">Numéro d’actif</Label>
                <Input id="asset_number" {...register("asset_number")} />
                {errors.asset_number && <p className="text-xs text-destructive">{errors.asset_number.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="type">Type</Label>
                <Input id="type" placeholder="Ordinateur portable" {...register("type")} />
                {errors.type && <p className="text-xs text-destructive">{errors.type.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="brand">Marque</Label>
                <Input id="brand" {...register("brand")} />
                {errors.brand && <p className="text-xs text-destructive">{errors.brand.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="model">Modèle</Label>
                <Input id="model" {...register("model")} />
                {errors.model && <p className="text-xs text-destructive">{errors.model.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="serial_number">Numéro de série</Label>
                <Input id="serial_number" {...register("serial_number")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="operating_system">Système d’exploitation</Label>
                <Input id="operating_system" {...register("operating_system")} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Service</Label>
              <Select value={watch("department_id")} onValueChange={(value) => setValue("department_id", value)}>
                <SelectTrigger><SelectValue placeholder="Sélectionner un service" /></SelectTrigger>
                <SelectContent>
                  {departments?.map((department) => (
                    <SelectItem key={department.id} value={String(department.id)}>{department.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Ajouter</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
