"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Paperclip, Send, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useCategories } from "@/hooks/use-reference-data";
import { attachmentsApi, getErrorMessage, ticketsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

// La priorité n'est plus choisie par l'utilisateur (elle est fixée par défaut
// à la création, voir backend/app/routers/tickets.py:create_ticket) et le
// champ "Équipement concerné" a été retiré du formulaire — les deux restent
// modifiables uniquement par Responsable IT/Administrateur après coup pour
// la priorité, et le lien ticket-équipement reste consultable depuis la
// fiche équipement (fonctionnalité distincte, non concernée par ce retrait).
const ticketSchema = z.object({
  title: z.string().min(3, "Le titre doit contenir au moins 3 caractères."),
  description: z.string().min(1, "La description est obligatoire."),
  category_id: z.string().min(1, "Merci de choisir une catégorie."),
  subcategory_id: z.string().optional(),
});

type TicketFormValues = z.infer<typeof ticketSchema>;

export default function NewTicketPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();
  const { data: categories } = useCategories();
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

  const onSubmit = async (values: TicketFormValues) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const finalCategoryId = values.subcategory_id ? Number(values.subcategory_id) : Number(values.category_id);
      const response = await ticketsApi.create({
        title: values.title,
        description: values.description,
        category_id: finalCategoryId,
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

        {/* Section 2 — Informations complémentaires */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations complémentaires</CardTitle>
            <CardDescription>Facultatif, mais utile pour accélérer le traitement.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
