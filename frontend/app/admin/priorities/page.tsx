"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Tags, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { PriorityBadge } from "@/components/tickets/priority-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import { usePriorities } from "@/hooks/use-reference-data";
import { getErrorMessage, prioritiesApi } from "@/lib/api";

const schema = z.object({
  name: z.string().min(1, "Le nom est obligatoire."),
  level: z.string().min(1, "Le niveau est obligatoire."),
});
type FormValues = z.infer<typeof schema>;

export default function AdminPrioritiesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: priorities, isLoading } = usePriorities();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await prioritiesApi.create({ name: values.name, level: Number(values.level) });
      toast({ title: "Priorité créée avec succès." });
      queryClient.invalidateQueries({ queryKey: ["priorities"] });
      setIsOpen(false);
      reset();
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!toDelete) return;
    try {
      await prioritiesApi.remove(toDelete);
      queryClient.invalidateQueries({ queryKey: ["priorities"] });
      toast({ title: "Priorité supprimée." });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    }
  };

  return (
    <div>
      <PageHeader title="Priorités" description="Niveaux de priorité utilisés pour trier les tickets." actions={<Button onClick={() => setIsOpen(true)}><Plus /> Nouvelle priorité</Button>} />
      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !priorities || priorities.length === 0 ? (
          <EmptyState icon={Tags} title="Aucune priorité" />
        ) : (
          <Table>
            <TableHeader><TableRow><TableHead>Nom</TableHead><TableHead>Niveau</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {[...priorities].sort((a, b) => a.level - b.level).map((priority) => (
                <TableRow key={priority.id}>
                  <TableCell><PriorityBadge name={priority.name} /></TableCell>
                  <TableCell>{priority.level}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setToDelete(priority.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nouvelle priorité</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="name">Nom</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="level">Niveau (1 = le plus bas)</Label>
              <Input id="level" type="number" min={1} max={10} {...register("level")} />
              {errors.level && <p className="text-xs text-destructive">{errors.level.message}</p>}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Créer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog open={!!toDelete} onOpenChange={(open) => !open && setToDelete(null)} title="Supprimer cette priorité ?" variant="destructive" confirmLabel="Supprimer" onConfirm={handleDelete} />
    </div>
  );
}
