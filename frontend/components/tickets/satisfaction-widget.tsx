"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Star } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { getErrorMessage, satisfactionApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export function SatisfactionWidget({ ticketId }: { ticketId: number }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: existingRating, isLoading } = useQuery({
    queryKey: ["tickets", ticketId, "satisfaction"],
    queryFn: () => satisfactionApi.get(ticketId).then((res) => res.data),
  });

  if (isLoading) return null;

  if (existingRating) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Votre évaluation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((value) => (
              <Star key={value} className={cn("h-5 w-5", value <= existingRating.rating ? "fill-amber-400 text-amber-400" : "text-muted-foreground")} />
            ))}
          </div>
          {existingRating.comment && <p className="mt-2 text-sm text-muted-foreground">« {existingRating.comment} »</p>}
        </CardContent>
      </Card>
    );
  }

  const handleSubmit = async () => {
    if (rating === 0) return;
    setIsSubmitting(true);
    try {
      await satisfactionApi.create(ticketId, { rating, comment: comment || undefined });
      queryClient.invalidateQueries({ queryKey: ["tickets", ticketId, "satisfaction"] });
      toast({ title: "Merci pour votre évaluation !" });
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Votre problème a-t-il été résolu ?</CardTitle>
        <CardDescription>Votre avis nous aide à améliorer la qualité du support.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setRating(value)}
              onMouseEnter={() => setHoverRating(value)}
              onMouseLeave={() => setHoverRating(0)}
              className="p-0.5"
              aria-label={`${value} étoile(s)`}
            >
              <Star
                className={cn(
                  "h-7 w-7 transition-colors",
                  value <= (hoverRating || rating) ? "fill-amber-400 text-amber-400" : "text-muted-foreground",
                )}
              />
            </button>
          ))}
        </div>
        <Textarea placeholder="Ajouter un commentaire (optionnel)…" rows={2} value={comment} onChange={(event) => setComment(event.target.value)} />
        <Button onClick={handleSubmit} disabled={rating === 0 || isSubmitting} size="sm">
          {isSubmitting && <Loader2 className="animate-spin" />}
          Envoyer mon évaluation
        </Button>
      </CardContent>
    </Card>
  );
}
