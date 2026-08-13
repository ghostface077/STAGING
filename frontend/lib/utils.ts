import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Fusionne intelligemment des classes Tailwind (évite les conflits de classes). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formate une date ISO en date française lisible (ex : 10 août 2026). */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

/** Formate une date ISO avec l'heure (ex : 10 août 2026 à 14:32). */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Formate une date de façon relative courte (ex : "il y a 5 min", "il y a 2 j"). */
export function formatRelativeTime(value: string): string {
  const date = new Date(value);
  const diffMs = date.getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / 60000);
  const rtf = new Intl.RelativeTimeFormat("fr-FR", { numeric: "auto" });

  if (Math.abs(diffMinutes) < 60) return rtf.format(diffMinutes, "minute");
  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 24) return rtf.format(diffHours, "hour");
  const diffDays = Math.round(diffHours / 24);
  return rtf.format(diffDays, "day");
}

/** Formate une taille de fichier en octets vers une unité lisible (Ko, Mo...). */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

/** Formate une durée en minutes vers un texte lisible (ex : "2 h 15 min", "45 min"). */
export function formatDurationMinutes(totalMinutes: number): string {
  const sign = totalMinutes < 0 ? "-" : "";
  const abs = Math.abs(totalMinutes);
  const hours = Math.floor(abs / 60);
  const minutes = Math.round(abs % 60);
  if (hours === 0) return `${sign}${minutes} min`;
  return `${sign}${hours} h ${minutes.toString().padStart(2, "0")} min`;
}

/** Retourne les initiales d'un utilisateur pour les avatars (ex : "Jean Dupont" → "JD"). */
export function getInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}
