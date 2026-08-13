"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Trash2, Users } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { useTeams, useTechnicians } from "@/hooks/use-reference-data";
import { getErrorMessage, teamsApi } from "@/lib/api";
import { getInitials } from "@/lib/utils";

const teamSchema = z.object({
  name: z.string().min(1, "Le nom de l'équipe est obligatoire."),
  description: z.string().optional(),
});
type TeamFormValues = z.infer<typeof teamSchema>;

export default function TeamsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: teams, isLoading } = useTeams();
  const { data: technicians } = useTechnicians();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [memberIds, setMemberIds] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [teamToDelete, setTeamToDelete] = useState<number | null>(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<TeamFormValues>({ resolver: zodResolver(teamSchema) });

  const toggleMember = (id: number) => {
    setMemberIds((prev) => (prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]));
  };

  const onSubmit = async (values: TeamFormValues) => {
    setIsSubmitting(true);
    try {
      await teamsApi.create({ name: values.name, description: values.description, member_ids: memberIds });
      toast({ title: "Équipe créée avec succès." });
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      setIsCreateOpen(false);
      reset();
      setMemberIds([]);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!teamToDelete) return;
    await teamsApi.remove(teamToDelete);
    queryClient.invalidateQueries({ queryKey: ["teams"] });
    toast({ title: "Équipe supprimée." });
  };

  return (
    <div>
      <PageHeader
        title="Équipes"
        description="Organisez vos techniciens en équipes de support."
        actions={<Button onClick={() => setIsCreateOpen(true)}><Plus /> Nouvelle équipe</Button>}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-40" />)}
        </div>
      ) : !teams || teams.length === 0 ? (
        <EmptyState icon={Users} title="Aucune équipe" description="Créez votre première équipe de support." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {teams.map((team) => (
            <Card key={team.id}>
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="text-base">{team.name}</CardTitle>
                  {team.description && <p className="mt-1 text-sm text-muted-foreground">{team.description}</p>}
                </div>
                <Button variant="ghost" size="icon" className="text-destructive" onClick={() => setTeamToDelete(team.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Membres ({team.members.length})</p>
                <div className="flex flex-wrap gap-2">
                  {team.members.length === 0 && <span className="text-sm text-muted-foreground">Aucun membre</span>}
                  {team.members.map((member) => (
                    <Badge key={member.id} variant="secondary" className="gap-1.5 py-1">
                      <Avatar className="h-4 w-4"><AvatarFallback className="text-[8px]">{getInitials(member.first_name, member.last_name)}</AvatarFallback></Avatar>
                      {member.first_name} {member.last_name}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nouvelle équipe</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <Label htmlFor="name">Nom de l’équipe</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" rows={2} {...register("description")} />
            </div>
            <div className="space-y-1.5">
              <Label>Membres</Label>
              <div className="max-h-40 space-y-2 overflow-y-auto rounded-md border border-border p-2">
                {technicians?.map((technician) => (
                  <label key={technician.id} className="flex cursor-pointer items-center gap-2 text-sm">
                    <Checkbox checked={memberIds.includes(technician.id)} onCheckedChange={() => toggleMember(technician.id)} />
                    {technician.first_name} {technician.last_name}
                  </label>
                ))}
                {!technicians?.length && <p className="text-xs text-muted-foreground">Aucun technicien disponible.</p>}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Créer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!teamToDelete}
        onOpenChange={(open) => !open && setTeamToDelete(null)}
        title="Supprimer cette équipe ?"
        description="Les tickets liés à cette équipe ne seront pas supprimés."
        variant="destructive"
        confirmLabel="Supprimer"
        onConfirm={handleDelete}
      />
    </div>
  );
}
