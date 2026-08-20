"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BookOpen, Eye, Loader2, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useCategories } from "@/hooks/use-reference-data";
import { getErrorMessage, knowledgeBaseApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const PAGE_SIZE = 20;

const articleSchema = z.object({
  title: z.string().min(1, "Le titre est obligatoire."),
  content: z.string().min(1, "Le contenu est obligatoire."),
  category_id: z.string().optional(),
});
type ArticleFormValues = z.infer<typeof articleSchema>;

export default function KnowledgeBasePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: categories } = useCategories();
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isStaff = user?.role?.name && ["Technicien", "Responsable IT", "Administrateur"].includes(user.role.name);

  const { data, isLoading } = useQuery({
    queryKey: ["knowledge-base", { search, categoryId, page }],
    queryFn: () =>
      knowledgeBaseApi
        .list({ search: search || undefined, category_id: categoryId ?? undefined, page, page_size: PAGE_SIZE })
        .then((res) => res.data),
    placeholderData: (previous) => previous,
  });
  const articles = data?.items;

  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<ArticleFormValues>({
    resolver: zodResolver(articleSchema),
  });

  const onSubmit = async (values: ArticleFormValues) => {
    setIsSubmitting(true);
    try {
      await knowledgeBaseApi.create({
        title: values.title,
        content: values.content,
        category_id: values.category_id ? Number(values.category_id) : null,
        status: "Publié",
      });
      toast({ title: "Article publié avec succès." });
      queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
      setIsDialogOpen(false);
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
        title="Base de connaissances"
        description="Solutions et procédures pour résoudre les problèmes courants."
        actions={
          isStaff ? (
            <Button onClick={() => setIsDialogOpen(true)}>
              <Plus /> Nouvel article
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
          placeholder="Rechercher un article…"
          className="pl-8"
        />
      </div>

      {categories && categories.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            onClick={() => { setCategoryId(null); setPage(1); }}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              categoryId === null ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            Toutes les catégories
          </button>
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => { setCategoryId(category.id); setPage(1); }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                categoryId === category.id ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground hover:text-foreground",
              )}
            >
              {category.name}
            </button>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-32" />)}
        </div>
      ) : !articles || articles.length === 0 ? (
        <EmptyState icon={BookOpen} title="Aucun article trouvé" description="Aucun article ne correspond à votre recherche." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article, index) => (
            <motion.div
              key={article.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18, delay: Math.min(index, 8) * 0.03, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -2 }}
            >
              <Link href={`/knowledge-base/${article.id}`}>
                <Card className="h-full shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
                  <CardContent className="flex h-full flex-col p-4">
                    {article.category && <Badge variant="secondary" className="mb-2 w-fit">{article.category.name}</Badge>}
                    <p className="font-medium leading-snug">{article.title}</p>
                    <p className="mt-1 line-clamp-3 flex-1 text-sm text-muted-foreground">{article.content}</p>
                    <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {article.views} vues</span>
                      {article.status !== "Publié" && <Badge variant="outline">{article.status}</Badge>}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      <Pagination page={page} pageCount={data?.pages ?? 1} onPageChange={setPage} totalItems={data?.total} pageSize={PAGE_SIZE} />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Nouvel article de la base de connaissances</DialogTitle>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="title">Titre</Label>
              <Input id="title" {...register("title")} />
              {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Catégorie</Label>
              <Select value={watch("category_id")} onValueChange={(value) => setValue("category_id", value)}>
                <SelectTrigger><SelectValue placeholder="Sélectionner (optionnel)" /></SelectTrigger>
                <SelectContent>
                  {categories?.map((category) => (
                    <SelectItem key={category.id} value={String(category.id)}>{category.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="content">Contenu</Label>
              <Textarea id="content" rows={8} placeholder="1. Première étape...&#10;2. Deuxième étape..." {...register("content")} />
              {errors.content && <p className="text-xs text-destructive">{errors.content.message}</p>}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Publier</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
