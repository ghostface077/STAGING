/**
 * Miroir de backend/app/services/ticket_state_machine.py (correctif #13) :
 * Résolu et Fermé ne sont jamais atteints ni quittés par une simple
 * transition de statut, seulement via les actions dédiées Résoudre / Fermer
 * / Réouvrir, seules à synchroniser correctement resolved_at/closed_at.
 *
 * Source unique — utilisée par TicketActions (menu « Changer le statut ») et
 * par TicketKanban (glisser-déposer), pour ne jamais diverger entre les deux.
 * Ce n'est qu'un confort d'affichage : la validation réelle reste côté serveur.
 */
export const ALLOWED_STATUS_TRANSITIONS: Record<string, string[]> = {
  "Nouveau": ["Ouvert", "En cours", "En attente", "Annulé"],
  "Ouvert": ["En cours", "En attente", "Annulé"],
  "En cours": ["En attente", "Ouvert", "Annulé"],
  "En attente": ["En cours", "Ouvert", "Annulé"],
  "Réouvert": ["En cours", "En attente", "Ouvert", "Annulé"],
  "Annulé": [],
};

/** Statuts gérés exclusivement par des actions dédiées (jamais par un simple changement de statut). */
export const MANAGED_ELSEWHERE_STATUSES = new Set(["Résolu", "Fermé"]);

export function canTransition(from: string, to: string): boolean {
  return (ALLOWED_STATUS_TRANSITIONS[from] ?? []).includes(to);
}
