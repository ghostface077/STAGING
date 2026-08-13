"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Timer, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import { usePriorities, useSlas } from "@/hooks/use-reference-data";
import { getErrorMessage, slasApi } from "@/lib/api";

const schema = z.object({
  name: z.string().min(1, "Le nom est obligatoire."),
  priority_id: z.string().min(1, "La priorité est obligatoire."),
  first_response_minutes: z.string().min(1, "Le délai de première réponse est obligatoire."),
  resolution_minutes: z.string().min(1, "Le délai de résolution est obligatoire."),
});
type FormValues = z.infer<typeof schema>;

export default function AdminSlasPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: slas, isLoading } = useSlas();
  const { data: priorities } = usePriorities();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await slasApi.create({
        name: values.name,
        priority_id: Number(values.priority_id),
        first_response_minutes: Number(values.first_response_minutes),
        resolution_minutes: Number(values.resolution_minutes),
        is_active: true,
      });
      toast({ title: "SLA créé avec succès." });
      queryClient.invalidateQueries({ queryKey: ["slas"] });
      setIsOpen(false);
      reset();
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleActive = async (id: number, isActive: boolean) => {
    await slasApi.update(id, { is_active: !isActive });
    queryClient.invalidateQueries({ queryKey: ["slas"] });
  };

  const handleDelete = async () => {
    if (!toDelete) return;
    try {
      await slasApi.remove(toDelete);
      queryClient.invalidateQueries({ queryKey: ["slas"] });
      toast({ title: "SLA supprimé." });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    }
  };

  return (
    <div>
      <PageHeader title="SLA" description="Délais de première réponse et de résolution par priorité." actions={<Button onClick={() => setIsOpen(true)}><Plus /> Nouveau SLA</Button>} />
      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !slas || slas.length === 0 ? (
          <EmptyState icon={Timer} title="Aucun SLA configuré" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Priorité</TableHead>
                <TableHead>1ère réponse</TableHead>
                <TableHead>Résolution</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {slas.map((sla) => (
                <TableRow key={sla.id}>
                  <TableCell className="font-medium">{sla.name}</TableCell>
                  <TableCell>{sla.priority?.name}</TableCell>
                  <TableCell>{sla.first_response_minutes} min</TableCell>
                  <TableCell>{Math.round(sla.resolution_minutes / 60)} h</TableCell>
                  <TableCell>
                    <button onClick={() => toggleActive(sla.id, sla.is_active)}>
                      <Badge variant={sla.is_active ? "success" : "outline"} className="cursor-pointer">{sla.is_active ? "Actif" : "Inactif"}</Badge>
                    </button>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setToDelete(sla.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nouveau SLA</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="name">Nom</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Priorité associée</Label>
              <Select value={watch("priority_id")} onValueChange={(value) => setValue("priority_id", value)}>
                <SelectTrigger><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                <SelectContent>
                  {priorities?.map((priority) => <SelectItem key={priority.id} value={String(priority.id)}>{priority.name}</SelectItem>)}
                </SelectContent>
              </Select>
              {errors.priority_id && <p className="text-xs text-destructive">{errors.priority_id.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="first_response_minutes">1ère réponse (min)</Label>
                <Input id="first_response_minutes" type="number" min={1} {...register("first_response_minutes")} />
                {errors.first_response_minutes && <p className="text-xs text-destructive">{errors.first_response_minutes.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="resolution_minutes">Résolution (min)</Label>
                <Input id="resolution_minutes" type="number" min={1} {...register("resolution_minutes")} />
                {errors.resolution_minutes && <p className="text-xs text-destructive">{errors.resolution_minutes.message}</p>}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Créer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog open={!!toDelete} onOpenChange={(open) => !open && setToDelete(null)} title="Supprimer ce SLA ?" variant="destructive" confirmLabel="Supprimer" onConfirm={handleDelete} />
    </div>
  );
}
