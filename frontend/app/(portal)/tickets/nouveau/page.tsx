"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Laptop, Loader2, Paperclip, Send, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { PriorityBadge } from "@/components/tickets/priority-badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useCategories, useEquipmentList, usePriorities } from "@/hooks/use-reference-data";
import { attachmentsApi, getErrorMessage, ticketsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const PRIORITY_DESCRIPTIONS: Record<string, string> = {
  "Critique": "Incident majeur nécessitant une intervention immédiate.",
  "Haute": "Problème important impactant fortement votre activité.",
  "Normale": "Problème standard, à traiter dans des délais habituels.",
  "Basse": "Demande non urgente.",
};

const ticketSchema = z.object({
  title: z.string().min(3, "Le titre doit contenir au moins 3 caractères."),
  description: z.string().min(1, "La description est obligatoire."),
  category_id: z.string().min(1, "Merci de choisir une catégorie."),
  subcategory_id: z.string().optional(),
  priority_id: z.string().min(1, "Merci de choisir une priorité."),
  equipment_id: z.string().optional(),
});

type TicketFormValues = z.infer<typeof ticketSchema>;

export default function NewTicketPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();
  const { data: categories } = useCategories();
  const { data: priorities } = usePriorities();
  const { data: equipments } = useEquipmentList();

  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  // Règle métier : seul le rôle Utilisateur crée des tickets. Un accès direct par URL
  // depuis un autre rôle est redirigé — le backend refuse de toute façon la création (403).
  const isAllowed = user?.role?.name === "Utilisateur";

  useEffect(() => {
    if (user && !isAllowed) {
      toast({
        title: "Action non autorisée",
        description: "La création de ticket est réservée aux utilisateurs. Votre rôle permet de traiter les tickets existants.",
        variant: "destructive",
      });
      router.replace("/tickets");
    }
  }, [user, isAllowed, router, toast]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TicketFormValues>({ resolver: zodResolver(ticketSchema) });

  const selectedCategoryId = watch("category_id");
  const selectedCategory = categories?.find((category) => String(category.id) === selectedCategoryId);
  const subcategories = selectedCategory?.children ?? [];
  const selectedPriority = priorities?.find((priority) => String(priority.id) === watch("priority_id"));

  const onSubmit = async (values: TicketFormValues) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const finalCategoryId = values.subcategory_id ? Number(values.subcategory_id) : Number(values.category_id);
      const response = await ticketsApi.create({
        title: values.title,
        description: values.description,
        category_id: finalCategoryId,
        priority_id: Number(values.priority_id),
        equipment_id: values.equipment_id ? Number(values.equipment_id) : null,
      });

      if (file) {
        await attachmentsApi.upload(response.data.id, file);
      }

      toast({
        title: "Ticket créé avec succès",
        description: `Votre ticket ${response.data.reference} a été créé avec succès.`,
      });
      router.push(`/tickets/${response.data.id}`);
    } catch (error) {
      setServerError(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isAllowed) {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="Action non autorisée"
        description="La création de ticket est réservée aux utilisateurs. Redirection en cours…"
      />
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Nouveau ticket" description="Décrivez votre incident ou votre demande le plus précisément possible." />

      <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
        {serverError && (
          <Alert variant="destructive">
            <AlertDescription>{serverError}</AlertDescription>
          </Alert>
        )}

        {/* Section 1 — Le problème */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Le problème</CardTitle>
            <CardDescription>Quel est votre incident ou votre demande ?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="title">Titre</Label>
              <Input id="title" placeholder="Ex : Imprimante hors service au 2e étage" {...register("title")} />
              {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" rows={5} placeholder="Décrivez le problème rencontré, les étapes pour le reproduire, etc." {...register("description")} />
              {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Catégorie</Label>
                <Select
                  value={selectedCategoryId}
                  onValueChange={(value) => { setValue("category_id", value); setValue("subcategory_id", undefined); }}
                >
                  <SelectTrigger><SelectValue placeholder="Sélectionner une catégorie" /></SelectTrigger>
                  <SelectContent>
                    {categories?.map((category) => (
                      <SelectItem key={category.id} value={String(category.id)}>{category.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.category_id && <p className="text-xs text-destructive">{errors.category_id.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label>Sous-catégorie</Label>
                <Select value={watch("subcategory_id")} onValueChange={(value) => setValue("subcategory_id", value)} disabled={subcategories.length === 0}>
                  <SelectTrigger>
                    <SelectValue placeholder={!selectedCategoryId ? "Sélectionnez d'abord une catégorie" : subcategories.length ? "Sélectionner (optionnel)" : "Aucune sous-catégorie disponible"} />
                  </SelectTrigger>
                  <SelectContent>
                    {subcategories.map((sub) => (
                      <SelectItem key={sub.id} value={String(sub.id)}>{sub.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 2 — Priorité */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Priorité</CardTitle>
            <CardDescription>Quel est le niveau d’urgence de cette demande ?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {priorities?.map((priority) => {
                const isSelected = String(priority.id) === watch("priority_id");
                return (
                  <button
                    type="button"
                    key={priority.id}
                    onClick={() => setValue("priority_id", String(priority.id))}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      isSelected ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border hover:bg-accent"
                    }`}
                  >
                    <PriorityBadge name={priority.name} />
                  </button>
                );
              })}
            </div>
            {selectedPriority && (
              <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {PRIORITY_DESCRIPTIONS[selectedPriority.name] ?? selectedPriority.description}
              </p>
            )}
            {errors.priority_id && <p className="text-xs text-destructive">{errors.priority_id.message}</p>}
          </CardContent>
        </Card>

        {/* Section 3 — Informations complémentaires */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations complémentaires</CardTitle>
            <CardDescription>Facultatif, mais utile pour accélérer le traitement.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="flex items-center gap-1.5"><Laptop className="h-3.5 w-3.5" /> Équipement concerné</Label>
              <Select value={watch("equipment_id")} onValueChange={(value) => setValue("equipment_id", value)} disabled={!equipments?.length}>
                <SelectTrigger><SelectValue placeholder={equipments?.length ? "Sélectionner (optionnel)" : "Aucun équipement associé à votre compte"} /></SelectTrigger>
                <SelectContent>
                  {equipments?.map((equipment) => (
                    <SelectItem key={equipment.id} value={String(equipment.id)}>
                      {equipment.asset_number} — {equipment.brand} {equipment.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="attachment" className="flex items-center gap-1.5"><Paperclip className="h-3.5 w-3.5" /> Pièce jointe</Label>
              <Input id="attachment" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="cursor-pointer" />
              <p className="text-xs text-muted-foreground">Formats acceptés : images, PDF, documents bureautiques (15 Mo max).</p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2 pb-4">
          <Button type="button" variant="outline" onClick={() => router.back()}>Annuler</Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <Loader2 className="animate-spin" /> : <Send />}
            Créer le ticket
          </Button>
        </div>
      </form>
    </div>
  );
}
