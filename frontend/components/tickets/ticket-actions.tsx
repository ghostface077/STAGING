"use client";

import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, Loader2, RotateCcw, UserPlus, Workflow, XCircle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { usePriorities, useStatuses, useTeams, useTechnicians } from "@/hooks/use-reference-data";
import { getErrorMessage, ticketsApi } from "@/lib/api";
import { ALLOWED_STATUS_TRANSITIONS, MANAGED_ELSEWHERE_STATUSES as CLOSED } from "@/lib/ticket-transitions";
import type { Ticket } from "@/lib/types";

interface TicketActionsProps {
  ticket: Ticket;
  currentUserId: number;
  role: string;
}

const isManager = (role: string) => role === "Responsable IT" || role === "Administrateur";
const isStaff = (role: string) => role === "Technicien" || isManager(role);

export function TicketActions({ ticket, currentUserId, role }: TicketActionsProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [dialog, setDialog] = useState<"assign" | "status" | "priority" | "resolve" | "escalate" | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["tickets", ticket.id] });
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
  };

  const runAction = async (label: string, action: () => Promise<unknown>) => {
    setIsSubmitting(true);
    try {
      await action();
      toast({ title: label });
      invalidate();
      setDialog(null);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const isOwner = ticket.requester.id === currentUserId;
  const canTakeTicket = role === "Technicien" && !ticket.technician;
  const canManageWorkflow = isStaff(role);
  const canClose = canManageWorkflow || isOwner;
  const canReopen = (canManageWorkflow || isOwner) && CLOSED.has(ticket.status.name);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {canTakeTicket && (
        <Button
          size="sm"
          onClick={() => runAction("Ticket pris en charge.", () => ticketsApi.assign(ticket.id, { technician_id: currentUserId }))}
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="animate-spin" /> : <UserPlus />}
          Prendre en charge
        </Button>
      )}

      {canManageWorkflow && ticket.status.name !== "Résolu" && (
        <Button size="sm" variant="outline" onClick={() => setDialog("resolve")}>
          <CheckCircle2 /> Résoudre
        </Button>
      )}

      {canClose && !CLOSED.has(ticket.status.name) && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => runAction("Ticket fermé.", () => ticketsApi.close(ticket.id))}
          disabled={isSubmitting}
        >
          <XCircle /> Fermer
        </Button>
      )}

      {canReopen && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => runAction("Ticket réouvert.", () => ticketsApi.reopen(ticket.id))}
          disabled={isSubmitting}
        >
          <RotateCcw /> Réouvrir
        </Button>
      )}

      {canManageWorkflow && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="sm" variant="outline">
              Plus d’actions <ChevronDown className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {/* Résolu/Fermé : aucune transition disponible via ce menu, voir le bouton « Réouvrir » dédié. */}
            {!CLOSED.has(ticket.status.name) && (
              <DropdownMenuItem onSelect={() => setDialog("status")}>Changer le statut</DropdownMenuItem>
            )}
            <DropdownMenuItem onSelect={() => setDialog("priority")}>Changer la priorité</DropdownMenuItem>
            {isManager(role) && <DropdownMenuItem onSelect={() => setDialog("assign")}>Attribuer / réassigner</DropdownMenuItem>}
            <DropdownMenuItem onSelect={() => setDialog("escalate")}>
              <Workflow className="h-4 w-4" /> Escalader
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      <StatusDialog open={dialog === "status"} onOpenChange={() => setDialog(null)} ticket={ticket} onDone={invalidate} />
      <PriorityDialog open={dialog === "priority"} onOpenChange={() => setDialog(null)} ticket={ticket} onDone={invalidate} />
      <ResolveDialog open={dialog === "resolve"} onOpenChange={() => setDialog(null)} ticket={ticket} onDone={invalidate} />
      {isManager(role) && <AssignDialog open={dialog === "assign"} onOpenChange={() => setDialog(null)} ticket={ticket} onDone={invalidate} />}
      <EscalateDialog open={dialog === "escalate"} onOpenChange={() => setDialog(null)} ticket={ticket} onDone={invalidate} />
    </div>
  );
}

interface DialogBaseProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ticket: Ticket;
  onDone: () => void;
}

function StatusDialog({ open, onOpenChange, ticket, onDone }: DialogBaseProps) {
  const { data: statuses } = useStatuses();
  const { toast } = useToast();
  const [value, setValue] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const allowedNames = ALLOWED_STATUS_TRANSITIONS[ticket.status.name] ?? [];
  const options = statuses?.filter((status) => allowedNames.includes(status.name));

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await ticketsApi.changeStatus(ticket.id, Number(value));
      toast({ title: "Statut mis à jour." });
      onDone();
      onOpenChange(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Changer le statut</DialogTitle>
          <DialogDescription>Sélectionnez le nouveau statut du ticket {ticket.reference}.</DialogDescription>
        </DialogHeader>
        <Select value={value} onValueChange={setValue}>
          <SelectTrigger><SelectValue placeholder="Sélectionner un statut" /></SelectTrigger>
          <SelectContent>
            {options?.map((status) => (
              <SelectItem key={status.id} value={String(status.id)}>{status.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !value}>{isSubmitting && <Loader2 className="animate-spin" />} Valider</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PriorityDialog({ open, onOpenChange, ticket, onDone }: DialogBaseProps) {
  const { data: priorities } = usePriorities();
  const { toast } = useToast();
  const [value, setValue] = useState<string>(String(ticket.priority.id));
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await ticketsApi.changePriority(ticket.id, Number(value));
      toast({ title: "Priorité mise à jour." });
      onDone();
      onOpenChange(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Changer la priorité</DialogTitle>
          <DialogDescription>Le SLA du ticket {ticket.reference} sera automatiquement réévalué.</DialogDescription>
        </DialogHeader>
        <Select value={value} onValueChange={setValue}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {priorities?.map((priority) => (
              <SelectItem key={priority.id} value={String(priority.id)}>{priority.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Valider</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ResolveDialog({ open, onOpenChange, ticket, onDone }: DialogBaseProps) {
  const { toast } = useToast();
  const [solution, setSolution] = useState(ticket.solution ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!solution.trim()) return;
    setIsSubmitting(true);
    try {
      await ticketsApi.resolve(ticket.id, solution);
      toast({ title: "Ticket marqué comme résolu." });
      onDone();
      onOpenChange(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Résoudre le ticket</DialogTitle>
          <DialogDescription>Décrivez la solution apportée au ticket {ticket.reference}.</DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label htmlFor="solution">Solution</Label>
          <Textarea id="solution" rows={4} value={solution} onChange={(event) => setSolution(event.target.value)} />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !solution.trim()}>
            {isSubmitting && <Loader2 className="animate-spin" />} Marquer comme résolu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AssignDialog({ open, onOpenChange, ticket, onDone }: DialogBaseProps) {
  const { data: technicians } = useTechnicians();
  const { data: teams } = useTeams();
  const { toast } = useToast();
  const [technicianId, setTechnicianId] = useState<string>(ticket.technician ? String(ticket.technician.id) : "aucun");
  const [teamId, setTeamId] = useState<string>(ticket.team ? String(ticket.team.id) : "aucune");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await ticketsApi.assign(ticket.id, {
        technician_id: technicianId !== "aucun" ? Number(technicianId) : null,
        team_id: teamId !== "aucune" ? Number(teamId) : null,
      });
      toast({ title: "Ticket attribué." });
      onDone();
      onOpenChange(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Attribuer le ticket</DialogTitle>
          <DialogDescription>Choisissez un technicien et/ou une équipe pour le ticket {ticket.reference}.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Technicien</Label>
            <Select value={technicianId} onValueChange={setTechnicianId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="aucun">Non assigné</SelectItem>
                {technicians?.map((technician) => (
                  <SelectItem key={technician.id} value={String(technician.id)}>{technician.first_name} {technician.last_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Équipe</Label>
            <Select value={teamId} onValueChange={setTeamId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="aucune">Aucune équipe</SelectItem>
                {teams?.map((team) => (
                  <SelectItem key={team.id} value={String(team.id)}>{team.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Attribuer</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EscalateDialog({ open, onOpenChange, ticket, onDone }: DialogBaseProps) {
  const { data: teams } = useTeams();
  const { toast } = useToast();
  const [teamId, setTeamId] = useState<string>("aucune");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await ticketsApi.escalate(ticket.id, { team_id: teamId !== "aucune" ? Number(teamId) : null, reason: reason || undefined });
      toast({ title: "Ticket escaladé." });
      onDone();
      onOpenChange(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Escalader le ticket</DialogTitle>
          <DialogDescription>Transférez le ticket {ticket.reference} vers une autre équipe avec un motif.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Équipe cible</Label>
            <Select value={teamId} onValueChange={setTeamId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="aucune">Aucune équipe</SelectItem>
                {teams?.map((team) => (
                  <SelectItem key={team.id} value={String(team.id)}>{team.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="reason">Motif</Label>
            <Textarea id="reason" rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Expliquez la raison de l'escalade…" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Escalader</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
