"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { ListTree, Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useCategories } from "@/hooks/use-reference-data";
import { categoriesApi, getErrorMessage } from "@/lib/api";

const schema = z.object({ name: z.string().min(1, "Le nom est obligatoire."), description: z.string().optional(), parent_id: z.string().optional() });
type FormValues = z.infer<typeof schema>;

export default function AdminCategoriesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: categories, isLoading } = useCategories();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await categoriesApi.create({
        name: values.name,
        description: values.description || null,
        parent_id: values.parent_id ? Number(values.parent_id) : null,
      });
      toast({ title: "Catégorie créée avec succès." });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
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
      await categoriesApi.remove(toDelete);
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      toast({ title: "Catégorie supprimée." });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    }
  };

  return (
    <div>
      <PageHeader title="Catégories" description="Catégories et sous-catégories de tickets." actions={<Button onClick={() => setIsOpen(true)}><Plus /> Nouvelle catégorie</Button>} />

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}</div>
      ) : !categories || categories.length === 0 ? (
        <EmptyState icon={ListTree} title="Aucune catégorie" />
      ) : (
        <div className="space-y-3">
          {categories.map((category) => (
            <Card key={category.id} className="shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{category.name}</p>
                  <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setToDelete(category.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="sr-only">Supprimer la catégorie {category.name}</span>
                  </Button>
                </div>
                {category.description && <p className="text-sm text-muted-foreground">{category.description}</p>}
                {category.children.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {category.children.map((child) => (
                      <Badge key={child.id} variant="secondary" className="gap-1.5">
                        {child.name}
                        <button
                          onClick={() => setToDelete(child.id)}
                          className="rounded text-muted-foreground hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                          aria-label={`Supprimer la sous-catégorie ${child.name}`}
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nouvelle catégorie</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="name">Nom</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Catégorie parente (optionnel — laisser vide pour une catégorie racine)</Label>
              <Select value={watch("parent_id")} onValueChange={(value) => setValue("parent_id", value)}>
                <SelectTrigger><SelectValue placeholder="Aucune (catégorie racine)" /></SelectTrigger>
                <SelectContent>
                  {categories?.map((category) => (
                    <SelectItem key={category.id} value={String(category.id)}>{category.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
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

      <ConfirmDialog open={!!toDelete} onOpenChange={(open) => !open && setToDelete(null)} title="Supprimer cette catégorie ?" variant="destructive" confirmLabel="Supprimer" onConfirm={handleDelete} />
    </div>
  );
}
