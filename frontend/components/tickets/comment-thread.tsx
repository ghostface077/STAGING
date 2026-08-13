"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Lock, Paperclip, Send } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { attachmentsApi, commentsApi, getErrorMessage } from "@/lib/api";
import { formatDateTime, formatFileSize, getInitials } from "@/lib/utils";

interface CommentThreadProps {
  ticketId: number;
  canWriteInternal: boolean;
}

export function CommentThread({ ticketId, canWriteInternal }: CommentThreadProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [content, setContent] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: comments, isLoading } = useQuery({
    queryKey: ["tickets", ticketId, "comments"],
    queryFn: () => commentsApi.list(ticketId).then((res) => res.data),
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!content.trim()) return;
    setIsSubmitting(true);
    try {
      const response = await commentsApi.create(ticketId, { content, is_internal: isInternal });
      if (file) {
        await attachmentsApi.upload(ticketId, file, response.data.id);
      }
      setContent("");
      setFile(null);
      setIsInternal(false);
      queryClient.invalidateQueries({ queryKey: ["tickets", ticketId] });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Chargement de la conversation…</p>}
        {!isLoading && (!comments || comments.length === 0) && (
          <p className="text-sm text-muted-foreground">Aucun commentaire pour le moment.</p>
        )}
        {comments?.map((comment) => (
          <div
            key={comment.id}
            className={`flex gap-3 rounded-lg border p-3 ${comment.is_internal ? "border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40" : "border-border"}`}
          >
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarFallback>{getInitials(comment.user.first_name, comment.user.last_name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-medium">{comment.user.first_name} {comment.user.last_name}</p>
                {comment.is_internal && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-200 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                    <Lock className="h-2.5 w-2.5" /> Note interne
                  </span>
                )}
                <span className="text-xs text-muted-foreground">{formatDateTime(comment.created_at)}</span>
              </div>
              <p className="mt-1 whitespace-pre-wrap text-sm">{comment.content}</p>
              {comment.attachments.length > 0 && (
                <div className="mt-2 space-y-1">
                  {comment.attachments.map((attachment) => (
                    <a
                      key={attachment.id}
                      href={attachmentsApi.downloadUrl(attachment.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="flex w-fit items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1 text-xs hover:bg-accent"
                    >
                      <Paperclip className="h-3 w-3" /> {attachment.file_name} ({formatFileSize(attachment.file_size)})
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-2 border-t border-border pt-4">
        <Textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder={isInternal ? "Rédiger une note interne (non visible par le demandeur)…" : "Écrire un commentaire…"}
          rows={3}
        />
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <Input file={file} onChange={setFile} />
            {canWriteInternal && (
              <div className="flex items-center gap-2">
                <Checkbox id="is-internal" checked={isInternal} onCheckedChange={(checked) => setIsInternal(checked === true)} />
                <Label htmlFor="is-internal" className="cursor-pointer text-xs font-normal text-muted-foreground">
                  Note interne (visible uniquement par le support)
                </Label>
              </div>
            )}
          </div>
          <Button type="submit" size="sm" disabled={isSubmitting || !content.trim()}>
            {isSubmitting ? <Loader2 className="animate-spin" /> : <Send />}
            Envoyer
          </Button>
        </div>
      </form>
    </div>
  );
}

function Input({ file, onChange }: { file: File | null; onChange: (file: File | null) => void }) {
  return (
    <label className="flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
      <Paperclip className="h-3.5 w-3.5" />
      {file ? file.name : "Joindre un fichier"}
      <input type="file" className="hidden" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
    </label>
  );
}
