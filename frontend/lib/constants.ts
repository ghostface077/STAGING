/**
 * Constantes partagées : libellés, couleurs et palettes utilisées dans toute l'interface.
 * Centraliser ces valeurs évite les incohérences visuelles entre les pages.
 */
import type { RoleName, SLAState } from "@/lib/types";

export const ROLES: Record<RoleName, RoleName> = {
  Utilisateur: "Utilisateur",
  Technicien: "Technicien",
  "Responsable IT": "Responsable IT",
  Administrateur: "Administrateur",
};

export const ROLE_LABELS: Record<string, string> = {
  Utilisateur: "Utilisateur",
  Technicien: "Technicien",
  "Responsable IT": "Responsable IT",
  Administrateur: "Administrateur",
};

/**
 * Système de badges statut/priorité : un point coloré discret + un libellé texte sur fond neutre,
 * plutôt que des pastilles pleinement colorées (plus sobre, plus "produit premium").
 */
export const STATUS_DOT_COLORS: Record<string, string> = {
  "Nouveau": "bg-info",
  "Ouvert": "bg-primary",
  "En cours": "bg-warning",
  "En attente": "bg-orange-500",
  "Résolu": "bg-success",
  "Fermé": "bg-muted-foreground",
  "Réouvert": "bg-fuchsia-500",
  "Annulé": "bg-destructive",
};

export const PRIORITY_DOT_COLORS: Record<string, string> = {
  "Basse": "bg-muted-foreground",
  "Normale": "bg-info",
  "Haute": "bg-warning",
  "Critique": "bg-destructive",
};

// Conservées pour compatibilité : variantes "pastille pleine" encore utilisées ponctuellement (graphiques).
export const STATUS_COLORS: Record<string, string> = {
  "Nouveau": "bg-sky-100 text-sky-700 border-sky-200 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-900",
  "Ouvert": "bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-900",
  "En cours": "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900",
  "En attente": "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-900",
  "Résolu": "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-900",
  "Fermé": "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  "Réouvert": "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-900",
  "Annulé": "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900",
};

export const PRIORITY_COLORS: Record<string, string> = {
  "Basse": "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  "Normale": "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900",
  "Haute": "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-900",
  "Critique": "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900",
};

export const SLA_STATE_LABELS: Record<SLAState, string> = {
  normal: "Normal",
  attention: "Attention",
  critique: "Critique",
  depasse: "Dépassé",
  aucun: "Aucun SLA",
};

export const SLA_STATE_COLORS: Record<SLAState, string> = {
  normal: "bg-success",
  attention: "bg-warning",
  critique: "bg-orange-500",
  depasse: "bg-destructive",
  aucun: "bg-muted-foreground/40",
};

// Mêmes teintes que SLA_STATE_COLORS, en valeurs "stroke" CSS exploitables par SVG (jauge circulaire).
export const SLA_STATE_STROKE_COLORS: Record<SLAState, string> = {
  normal: "hsl(var(--success))",
  attention: "hsl(var(--warning))",
  critique: "#f97316",
  depasse: "hsl(var(--destructive))",
  aucun: "hsl(var(--muted-foreground) / 0.4)",
};

export const SLA_STATE_TEXT_COLORS: Record<SLAState, string> = {
  normal: "text-success",
  attention: "text-warning",
  critique: "text-orange-600 dark:text-orange-400",
  depasse: "text-destructive",
  aucun: "text-muted-foreground",
};

export const NOTIFICATION_TYPE_LABELS: Record<string, string> = {
  creation_ticket: "Création de ticket",
  attribution: "Attribution",
  nouveau_commentaire: "Nouveau commentaire",
  changement_statut: "Changement de statut",
  changement_priorite: "Changement de priorité",
  resolution: "Résolution",
  fermeture: "Fermeture",
  reouverture: "Réouverture",
  sla_bientot_depasse: "SLA bientôt dépassé",
  sla_depasse: "SLA dépassé",
};

export const HISTORY_ACTION_LABELS: Record<string, string> = {
  creation: "Création du ticket",
  modification: "Modification du ticket",
  attribution: "Attribution",
  prise_en_charge: "Prise en charge",
  changement_statut: "Changement de statut",
  changement_priorite: "Changement de priorité",
  commentaire: "Commentaire ajouté",
  resolution: "Résolution",
  fermeture: "Fermeture",
  reouverture: "Réouverture",
  escalade: "Escalade",
  ajout_piece_jointe: "Pièce jointe ajoutée",
};

// Note : TOKEN_STORAGE_KEY (session en localStorage) a été retiré au
// correctif #12 — la session est désormais portée par des cookies httpOnly
// posés par le serveur, plus rien à stocker côté client.
