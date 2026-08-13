"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Edit, Eye, EyeOff, Loader2, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { getErrorMessage, knowledgeBaseApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime } from "@/lib/utils";

export default function KnowledgeBaseDetailPage() {
  const params = useParams<{ id: string }>();
  const articleId = Number(params.id);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { user } = useAuth();
  const isStaff = user?.role?.name && ["Technicien", "Responsable IT", "Administrateur"].includes(user.role.name);

  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: article, isLoading } = useQuery({
    queryKey: ["knowledge-base", articleId],
    queryFn: () => knowledgeBaseApi.get(articleId).then((res) => res.data),
    enabled: Number.isFinite(articleId),
  });

  const openEdit = () => {
    if (!article) return;
    setTitle(article.title);
    setContent(article.content);
    setIsEditOpen(true);
  };

  const handleSave = async () => {
    setIsSubmitting(true);
    try {
      await knowledgeBaseApi.update(articleId, { title, content });
      queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
      toast({ title: "Article mis à jour." });
      setIsEditOpen(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePublish = async () => {
    if (!article) return;
    await knowledgeBaseApi.update(articleId, { status: article.status === "Publié" ? "Dépublié" : "Publié" });
    queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
  };

  const handleDelete = async () => {
    await knowledgeBaseApi.remove(articleId);
    toast({ title: "Article supprimé." });
    router.push("/knowledge-base");
  };

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!article) return <p className="text-sm text-destructive">Article introuvable.</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/knowledge-base" className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Retour à la base de connaissances
      </Link>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            {article.category && <Badge variant="secondary" className="mb-2">{article.category.name}</Badge>}
            <h1 className="text-xl font-semibold">{article.title}</h1>
            <p className="mt-1 text-xs text-muted-foreground">
              Par {article.author ? `${article.author.first_name} ${article.author.last_name}` : "Auteur inconnu"} · Mis à jour le {formatDateTime(article.updated_at)} ·{" "}
              <Eye className="inline h-3 w-3" /> {article.views} vues
            </p>
          </div>
          {isStaff && (
            <div className="flex shrink-0 gap-2">
              <Button variant="outline" size="sm" onClick={togglePublish}>
                {article.status === "Publié" ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                {article.status === "Publié" ? "Dépublier" : "Publier"}
              </Button>
              <Button variant="outline" size="sm" onClick={openEdit}><Edit className="h-3.5 w-3.5" /> Modifier</Button>
              <Button variant="outline" size="sm" onClick={() => setIsDeleteOpen(true)} className="text-destructive hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="whitespace-pre-wrap text-sm leading-relaxed">{article.content}</div>
        </CardContent>
      </Card>

      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>Modifier l’article</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-title">Titre</Label>
              <Input id="edit-title" value={title} onChange={(event) => setTitle(event.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-content">Contenu</Label>
              <Textarea id="edit-content" rows={10} value={content} onChange={(event) => setContent(event.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>Annuler</Button>
            <Button onClick={handleSave} disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Enregistrer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        title="Supprimer cet article ?"
        description="Cette action est irréversible."
        variant="destructive"
        confirmLabel="Supprimer"
        onConfirm={handleDelete}
      />
    </div>
  );
}
