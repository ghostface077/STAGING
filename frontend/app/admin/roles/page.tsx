"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, ShieldCheck, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useRoles } from "@/hooks/use-reference-data";
import { getErrorMessage, rolesApi } from "@/lib/api";

const roleSchema = z.object({ name: z.string().min(1, "Le nom est obligatoire."), description: z.string().optional() });
type RoleFormValues = z.infer<typeof roleSchema>;

export default function AdminRolesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: roles, isLoading } = useRoles();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<RoleFormValues>({ resolver: zodResolver(roleSchema) });

  const onSubmit = async (values: RoleFormValues) => {
    setIsSubmitting(true);
    try {
      await rolesApi.create(values);
      toast({ title: "Rôle créé avec succès." });
      queryClient.invalidateQueries({ queryKey: ["roles"] });
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
      await rolesApi.remove(toDelete);
      queryClient.invalidateQueries({ queryKey: ["roles"] });
      toast({ title: "Rôle supprimé." });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    }
  };

  return (
    <div>
      <PageHeader title="Rôles" description="Rôles applicatifs disponibles pour les utilisateurs." actions={<Button onClick={() => setIsOpen(true)}><Plus /> Nouveau rôle</Button>} />
      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !roles || roles.length === 0 ? (
          <EmptyState icon={ShieldCheck} title="Aucun rôle" />
        ) : (
          <Table>
            <TableHeader><TableRow><TableHead>Nom</TableHead><TableHead>Description</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {roles.map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">{role.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{role.description ?? "—"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setToDelete(role.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nouveau rôle</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="name">Nom</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" rows={2} {...register("description")} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Créer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(open) => !open && setToDelete(null)}
        title="Supprimer ce rôle ?"
        variant="destructive"
        confirmLabel="Supprimer"
        onConfirm={handleDelete}
      />
    </div>
  );
}
